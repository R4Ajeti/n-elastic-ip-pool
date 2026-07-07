import json
from http.client import HTTPException
from json import JSONDecodeError
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from n_elastic_ip_pool.constant.elastic_ip_pool_constant import (
    DEFAULT_TIMEOUT_SECOND_INT,
    GEONODE_FREE_PROXY_LIST_ANONYMITY_LEVEL_STR,
    GEONODE_FREE_PROXY_LIST_API_BASE_URL_STR,
    GEONODE_FREE_PROXY_LIST_LIMIT_INT,
    GEONODE_FREE_PROXY_LIST_MIN_UPTIME_INT,
    GEONODE_FREE_PROXY_LIST_PAGE_INT,
    GEONODE_FREE_PROXY_LIST_PROTOCOLS_STR,
    GEONODE_FREE_PROXY_LIST_SORT_BY_STR,
    GEONODE_FREE_PROXY_LIST_SORT_TYPE_STR,
    PROXY_TEST_USER_AGENT_STR,
)
from n_elastic_ip_pool.helper.proxy_address_format_helper import normalizeProxyAddress


class GeonodeFreeProxyListProxyError(RuntimeError):
    """Raised when the Geonode free proxy list provider request fails."""


class GeonodeFreeProxyListProxy:
    """External Geonode Free Proxy List API abstraction."""

    def __init__(
        self,
        baseUrlStr: str = GEONODE_FREE_PROXY_LIST_API_BASE_URL_STR,
        limitInt: int = GEONODE_FREE_PROXY_LIST_LIMIT_INT,
        pageInt: int = GEONODE_FREE_PROXY_LIST_PAGE_INT,
        sortByStr: str = GEONODE_FREE_PROXY_LIST_SORT_BY_STR,
        sortTypeStr: str = GEONODE_FREE_PROXY_LIST_SORT_TYPE_STR,
        protocolsStr: str = GEONODE_FREE_PROXY_LIST_PROTOCOLS_STR,
        anonymityLevelStr: str = GEONODE_FREE_PROXY_LIST_ANONYMITY_LEVEL_STR,
        minUpTimeInt: int = GEONODE_FREE_PROXY_LIST_MIN_UPTIME_INT,
        timeoutSecondInt: int = DEFAULT_TIMEOUT_SECOND_INT,
    ) -> None:
        self.baseUrlStr = baseUrlStr.rstrip("/")
        self.limitInt = int(limitInt)
        self.pageInt = int(pageInt)
        self.sortByStr = sortByStr
        self.sortTypeStr = sortTypeStr
        self.protocolsStr = protocolsStr
        self.anonymityLevelStr = anonymityLevelStr
        self.minUpTimeInt = int(minUpTimeInt)
        self.timeoutSecondInt = timeoutSecondInt

    def buildFetchUrl(self) -> str:
        queryParamStr = urlencode(
            [
                ("limit", str(self.limitInt)),
                ("page", str(self.pageInt)),
                ("sort_by", self.sortByStr),
                ("sort_type", self.sortTypeStr),
                ("protocols", self.protocolsStr),
                ("anonymityLevel", self.anonymityLevelStr),
                ("filterUpTime", str(self.minUpTimeInt)),
            ],
        )
        return f"{self.baseUrlStr}?{queryParamStr}"

    def fetchProxyCandidateText(self) -> dict:
        """Fetch Geonode JSON and return normalized internal candidate data."""
        urlStr = self.buildFetchUrl()
        request = Request(
            urlStr,
            method="GET",
            headers={
                "Accept": "application/json",
                "User-Agent": PROXY_TEST_USER_AGENT_STR,
            },
        )

        try:
            with urlopen(request, timeout=self.timeoutSecondInt) as response:
                responseTextStr = response.read().decode("utf-8")
                statusCodeInt = response.getcode()
        except HTTPError as error:
            raise GeonodeFreeProxyListProxyError(
                f"Geonode request failed with status {error.code}.",
            ) from error
        except (HTTPException, TimeoutError, URLError, OSError) as error:
            raise GeonodeFreeProxyListProxyError("Geonode request failed.") from error

        if statusCodeInt < 200 or statusCodeInt >= 300:
            raise GeonodeFreeProxyListProxyError(
                f"Geonode request failed with status {statusCodeInt}.",
            )

        parsedResultDict = self.parseProxyCandidateJson(responseTextStr)
        return {
            "url": urlStr,
            "status_code": statusCodeInt,
            **parsedResultDict,
        }

    def parseProxyCandidateJson(self, responseTextStr: str) -> dict:
        try:
            responseDict = json.loads(responseTextStr)
        except (JSONDecodeError, TypeError) as error:
            raise GeonodeFreeProxyListProxyError(
                "Geonode response was not valid JSON.",
            ) from error

        if not isinstance(responseDict, dict):
            raise GeonodeFreeProxyListProxyError(
                "Geonode response must be a JSON object.",
            )

        proxyRecordList = responseDict.get("data")
        if not isinstance(proxyRecordList, list):
            raise GeonodeFreeProxyListProxyError(
                "Geonode response data must be a list.",
            )

        proxyCandidateList = []
        proxyCandidateMetadataList = []
        seenProxySet = set()
        for proxyRecord in proxyRecordList:
            normalizedProxyRecordDict = self.normalizeProxyRecord(proxyRecord)
            if not normalizedProxyRecordDict:
                continue

            proxyStr = str(normalizedProxyRecordDict["proxy"])
            if proxyStr in seenProxySet:
                continue

            seenProxySet.add(proxyStr)
            proxyCandidateList.append(proxyStr)
            proxyCandidateMetadataList.append(normalizedProxyRecordDict)

        proxyCandidateTextStr = "".join(
            f"{proxyStr}\n"
            for proxyStr in proxyCandidateList
        )
        return {
            "proxy_candidate_text": proxyCandidateTextStr,
            "proxy_candidate_metadata_list": proxyCandidateMetadataList,
        }

    def normalizeProxyRecord(self, proxyRecord) -> dict | None:
        if not isinstance(proxyRecord, dict):
            return None

        ipValue = proxyRecord.get("ip")
        portValue = proxyRecord.get("port")
        if ipValue is None or portValue is None:
            return None

        proxyStr = normalizeProxyAddress(f"{ipValue}:{portValue}")
        if not proxyStr:
            return None

        allowedProtocolSet = self.getAllowedProtocolSet()
        protocolList = self.normalizeProtocolList(proxyRecord.get("protocols"))
        supportedProtocolList = [
            protocolStr
            for protocolStr in protocolList
            if protocolStr in allowedProtocolSet
        ]
        if not supportedProtocolList:
            return None

        normalizedProxyRecordDict = {
            "proxy": proxyStr,
            "protocols": supportedProtocolList,
        }
        for fieldNameStr in [
            "country",
            "anonymityLevel",
            "lastChecked",
            "updated_at",
            "google",
        ]:
            fieldValue = proxyRecord.get(fieldNameStr)
            if fieldValue is not None:
                normalizedProxyRecordDict[fieldNameStr] = fieldValue

        for fieldNameStr in ["upTime", "latency", "responseTime"]:
            numberValue = self.normalizeNumberValue(proxyRecord.get(fieldNameStr))
            if numberValue is not None:
                normalizedProxyRecordDict[fieldNameStr] = numberValue

        return normalizedProxyRecordDict

    def getAllowedProtocolSet(self) -> set[str]:
        return set(self.normalizeProtocolList(self.protocolsStr))

    def normalizeProtocolList(self, protocolValue) -> list[str]:
        if isinstance(protocolValue, str):
            rawProtocolList = protocolValue.split(",")
        elif isinstance(protocolValue, list):
            rawProtocolList = protocolValue
        else:
            return []

        protocolList = []
        for protocol in rawProtocolList:
            protocolStr = str(protocol).strip().lower()
            if protocolStr:
                protocolList.append(protocolStr)

        return protocolList

    def normalizeNumberValue(self, numberValue):
        if isinstance(numberValue, bool) or numberValue is None:
            return None

        if isinstance(numberValue, int):
            return numberValue

        if isinstance(numberValue, float):
            return numberValue

        try:
            normalizedNumberFloat = float(str(numberValue))
        except (TypeError, ValueError):
            return None

        if normalizedNumberFloat.is_integer():
            return int(normalizedNumberFloat)

        return normalizedNumberFloat
