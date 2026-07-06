import json
import random
from json import JSONDecodeError

from core.constant.elastic_ip_pool_constant import (
    DEFAULT_PROXY_CANDIDATE_LIMIT_INT,
    DEFAULT_PROXY_RELEASE_CHANNEL_STR,
    DEFAULT_PROXY_RESULT_COUNT_INT,
    DEFAULT_PROXY_SAVE_WORKING_PROXY_BOOL,
    DEFAULT_PROXY_SELECTION_MODE_STR,
    DEFAULT_PROXY_SHUFFLE_CANDIDATE_BOOL,
    DEFAULT_PROXY_USE_SAVED_PROXY_BOOL,
    KEY_VAL_MAX_SAVED_PROXY_COUNT_INT,
    KEY_VAL_MAX_VALUE_LENGTH_INT,
    KEY_VAL_DUMMY_PROXY_KEY_STR,
    KEY_VAL_DUMMY_PROXY_VALUE_STR,
    PROXY_SELECTION_MODE_RANDOM_STR,
    PROXY_MAX_TIMING_MILLISECOND_INT,
    PROXY_VALIDATION_SUCCESS_COUNT_INT,
)
from core.helper.proxy_address_format_helper import normalizeProxyAddress
from core.helper.string_hash_helper import hashStringValue
from core.proxy.elastic_ip_health_check_proxy import ElasticIpHealthCheckProxy
from core.proxy.key_val_store_proxy import KeyValStoreProxy, KeyValStoreProxyError
from core.proxy.proxy_scrape_proxy import ProxyScrapeProxy, ProxyScrapeProxyError
from core.repo.elastic_ip_pool_repo import ElasticIpPoolRepo


class ElasticIpPoolService:
    """Service for Elastic IP pool business rules."""

    def __init__(
        self,
        elasticIpPoolRepo: ElasticIpPoolRepo | None = None,
        elasticIpHealthCheckProxy: ElasticIpHealthCheckProxy | None = None,
        keyValStoreProxy: KeyValStoreProxy | None = None,
        proxyScrapeProxy: ProxyScrapeProxy | None = None,
        keyValStoreProxyStr: str = KEY_VAL_DUMMY_PROXY_KEY_STR,
        dummyProxyValueStr: str = KEY_VAL_DUMMY_PROXY_VALUE_STR,
        proxyValidationSuccessCountInt: int = PROXY_VALIDATION_SUCCESS_COUNT_INT,
        proxyMaxTimingMillisecondInt: int = PROXY_MAX_TIMING_MILLISECOND_INT,
        proxySelectionModeStr: str = DEFAULT_PROXY_SELECTION_MODE_STR,
        proxyResultCountInt: int = DEFAULT_PROXY_RESULT_COUNT_INT,
        proxyCandidateLimitInt: int = DEFAULT_PROXY_CANDIDATE_LIMIT_INT,
        proxyShuffleCandidateBool: bool = DEFAULT_PROXY_SHUFFLE_CANDIDATE_BOOL,
        proxyRandomSeedInt: int | None = None,
        useSavedProxyBool: bool = DEFAULT_PROXY_USE_SAVED_PROXY_BOOL,
        saveWorkingProxyBool: bool = DEFAULT_PROXY_SAVE_WORKING_PROXY_BOOL,
        releaseChannelStr: str = DEFAULT_PROXY_RELEASE_CHANNEL_STR,
    ) -> None:
        self.elasticIpPoolRepo = elasticIpPoolRepo or ElasticIpPoolRepo()
        self.elasticIpHealthCheckProxy = (
            elasticIpHealthCheckProxy or ElasticIpHealthCheckProxy()
        )
        self.keyValStoreProxy = keyValStoreProxy or KeyValStoreProxy()
        self.proxyScrapeProxy = proxyScrapeProxy or ProxyScrapeProxy()
        self.keyValStoreProxyStr = keyValStoreProxyStr
        self.dummyProxyValueStr = dummyProxyValueStr
        self.proxyValidationSuccessCountInt = max(
            1,
            int(proxyValidationSuccessCountInt or 1),
        )
        self.proxyMaxTimingMillisecondInt = max(
            1,
            int(proxyMaxTimingMillisecondInt or 1),
        )
        self.proxySelectionModeStr = self.normalizeProxySelectionMode(
            proxySelectionModeStr,
        )
        self.proxyResultCountInt = max(0, int(proxyResultCountInt or 0))
        self.proxyCandidateLimitInt = max(0, int(proxyCandidateLimitInt or 0))
        self.proxyShuffleCandidateBool = bool(proxyShuffleCandidateBool)
        self.proxyRandomSeedInt = proxyRandomSeedInt
        self.proxyRandom = random.Random(proxyRandomSeedInt)
        self.useSavedProxyBool = bool(useSavedProxyBool)
        self.saveWorkingProxyBool = bool(saveWorkingProxyBool)
        self.releaseChannelStr = str(
            releaseChannelStr or DEFAULT_PROXY_RELEASE_CHANNEL_STR,
        ).lower()
        self.rankedProxyDictList: list[dict] | None = None
        self.rankedProxyList: list[str] | None = None

    def get(self) -> str | None:
        if self.useSavedProxyBool:
            storedProxyValueStr = self.check()
            if storedProxyValueStr:
                return storedProxyValueStr

        return self.search()

    def check(self) -> str | None:
        keyValKeyStr = self.getKeyValProxyKey()
        try:
            resultDict = self.keyValStoreProxy.getValue(keyValKeyStr)
        except KeyValStoreProxyError:
            return None

        if not resultDict.get("exists") or not resultDict.get("value"):
            return None

        savedProxyList = self.parseSavedProxyList(str(resultDict["value"]))
        if not savedProxyList:
            return None

        workingProxyList = []
        for savedProxyDict in savedProxyList:
            testResultDict = self.testProxy(str(savedProxyDict["proxy"]))
            if self.isProxyTestResultUsable(testResultDict):
                workingProxyList.append(
                    self.buildWorkingProxyRecord(
                        str(testResultDict["proxy"]),
                        [self.getTimingMsInt(testResultDict)],
                        str(testResultDict["checkedAt"]),
                    ),
                )

        self.rankedProxyDictList = self.limitWorkingProxyList(
            self.rankWorkingProxyList(workingProxyList),
        )
        if not self.rankedProxyDictList:
            return None

        self.rankedProxyList = [
            str(proxyDict["proxy"])
            for proxyDict in self.rankedProxyDictList
        ]

        return str(self.rankedProxyDictList[0]["proxy"])

    def search(self) -> str | None:
        proxyCandidateTextStr = self.fetchProxyCandidateText()
        proxyCandidateList = self.parseProxyCandidateList(proxyCandidateTextStr)
        if not proxyCandidateList:
            return None

        workingProxyList = self.validateProxyCandidateList(proxyCandidateList)
        self.rankedProxyDictList = self.limitWorkingProxyList(
            self.rankWorkingProxyList(workingProxyList),
        )
        if not self.rankedProxyDictList:
            return None

        self.rankedProxyList = [
            str(proxyDict["proxy"])
            for proxyDict in self.rankedProxyDictList
        ]

        if self.saveWorkingProxyBool:
            try:
                self.saveWorkingProxyList(self.rankedProxyDictList)
            except (KeyValStoreProxyError, RuntimeError) as error:
                self.onWorkingProxySaveFailure(error)
        else:
            self.onWorkingProxySaveSkipped()

        return str(self.rankedProxyDictList[0]["proxy"])

    def update(self, valueStr: str) -> str:
        if valueStr is None:
            raise ValueError("valueStr is required before saving to KeyVal.")

        keyValKeyStr = self.getKeyValProxyKey()
        resultDict = self.keyValStoreProxy.setValue(
            keyValKeyStr,
            valueStr,
        )

        if not resultDict.get("stored"):
            raise RuntimeError("Proxy value was not stored in KeyVal.")

        return str(resultDict.get("value") or valueStr)

    def fetchProxyCandidateText(self) -> str:
        try:
            resultDict = self.proxyScrapeProxy.fetchProxyCandidateText()
        except ProxyScrapeProxyError:
            return ""

        statusCodeInt = int(resultDict.get("status_code") or 0)
        if statusCodeInt < 200 or statusCodeInt >= 300:
            return ""

        return str(resultDict.get("proxy_candidate_text") or "")

    def parseProxyCandidateList(self, proxyCandidateTextStr: str) -> list[str]:
        proxyCandidateList = []
        seenProxySet = set()

        for lineStr in proxyCandidateTextStr.splitlines():
            normalizedProxyStr = normalizeProxyAddress(lineStr)
            if not normalizedProxyStr or normalizedProxyStr in seenProxySet:
                continue

            seenProxySet.add(normalizedProxyStr)
            proxyCandidateList.append(normalizedProxyStr)

        return self.prepareProxyCandidateList(proxyCandidateList)

    def prepareProxyCandidateList(self, proxyCandidateList: list[str]) -> list[str]:
        preparedProxyCandidateList = list(proxyCandidateList)

        if self.proxyShuffleCandidateBool:
            self.proxyRandom.shuffle(preparedProxyCandidateList)

        if self.proxyCandidateLimitInt:
            return preparedProxyCandidateList[: self.proxyCandidateLimitInt]

        return preparedProxyCandidateList

    def parseSavedProxyList(self, savedValueStr: str) -> list[dict]:
        try:
            savedValue = json.loads(savedValueStr)
        except (JSONDecodeError, TypeError):
            return self.normalizeSavedProxyList(savedValueStr)

        return self.normalizeSavedProxyList(savedValue)

    def normalizeSavedProxyList(self, savedValue) -> list[dict]:
        if isinstance(savedValue, str):
            normalizedProxyStr = normalizeProxyAddress(savedValue)
            if not normalizedProxyStr:
                return []
            return [{"proxy": normalizedProxyStr}]

        if isinstance(savedValue, dict):
            normalizedProxyStr = normalizeProxyAddress(str(savedValue.get("proxy", "")))
            if not normalizedProxyStr:
                return []
            return [{**savedValue, "proxy": normalizedProxyStr}]

        if not isinstance(savedValue, list):
            return []

        proxyList = []
        seenProxySet = set()
        for savedProxy in savedValue:
            normalizedProxyList = self.normalizeSavedProxyList(savedProxy)
            if not normalizedProxyList:
                continue

            normalizedProxyDict = normalizedProxyList[0]
            proxyStr = str(normalizedProxyDict["proxy"])
            if proxyStr in seenProxySet:
                continue

            seenProxySet.add(proxyStr)
            proxyList.append(normalizedProxyDict)

        return proxyList

    def validateProxyCandidateList(self, proxyCandidateList: list[str]) -> list[dict]:
        proxyCheckByProxyDict = {
            proxyStr: {
                "proxy": proxyStr,
                "timingMsList": [],
                "lastCheckedAt": "",
            }
            for proxyStr in proxyCandidateList
        }

        for passNumberInt in range(1, self.proxyValidationSuccessCountInt + 1):
            if not proxyCheckByProxyDict:
                break

            self.onProxyValidationPassStart(passNumberInt)
            nextProxyCheckByProxyDict = {}

            for proxyStr, proxyCheckDict in proxyCheckByProxyDict.items():
                testResultDict = self.testProxy(proxyStr)
                if not self.isProxyTestResultUsable(testResultDict):
                    continue

                normalizedProxyStr = str(testResultDict["proxy"])
                proxyCheckDict["proxy"] = normalizedProxyStr
                proxyCheckDict["timingMsList"].append(self.getTimingMsInt(testResultDict))
                proxyCheckDict["lastCheckedAt"] = str(testResultDict["checkedAt"])
                nextProxyCheckByProxyDict[normalizedProxyStr] = proxyCheckDict

            self.onProxyValidationPassFinish(
                passNumberInt,
                len(nextProxyCheckByProxyDict),
            )
            proxyCheckByProxyDict = nextProxyCheckByProxyDict

        return [
            self.buildWorkingProxyRecord(
                str(proxyCheckDict["proxy"]),
                list(proxyCheckDict["timingMsList"]),
                str(proxyCheckDict["lastCheckedAt"]),
            )
            for proxyCheckDict in proxyCheckByProxyDict.values()
            if len(proxyCheckDict["timingMsList"]) >= self.proxyValidationSuccessCountInt
        ]

    def onProxyValidationPassStart(self, passNumberInt: int) -> None:
        return None

    def onProxyValidationPassFinish(
        self,
        passNumberInt: int,
        passedProxyCountInt: int,
    ) -> None:
        return None

    def retestProxyUntilReady(self, proxyCheckDict: dict) -> dict | None:
        while len(proxyCheckDict["timingMsList"]) < self.proxyValidationSuccessCountInt:
            testResultDict = self.testProxy(str(proxyCheckDict["proxy"]))
            if not self.isProxyTestResultUsable(testResultDict):
                return None

            proxyCheckDict["timingMsList"].append(self.getTimingMsInt(testResultDict))
            proxyCheckDict["lastCheckedAt"] = str(testResultDict["checkedAt"])

        return proxyCheckDict

    def testProxy(self, proxyStr: str) -> dict:
        return self.elasticIpHealthCheckProxy.testProxy(proxyStr)

    def isProxyTestResultUsable(self, testResultDict: dict) -> bool:
        if not testResultDict.get("isWorking"):
            return False

        return self.getTimingMsInt(testResultDict) <= self.proxyMaxTimingMillisecondInt

    def rankWorkingProxyList(self, workingProxyList: list[dict]) -> list[dict]:
        rankedWorkingProxyList = sorted(
            workingProxyList,
            key=lambda workingProxyDict: (
                int(workingProxyDict.get("averageTimingMs") or 0),
                str(workingProxyDict.get("proxy") or ""),
            ),
        )

        if self.proxySelectionModeStr == PROXY_SELECTION_MODE_RANDOM_STR:
            self.proxyRandom.shuffle(rankedWorkingProxyList)

        return rankedWorkingProxyList

    def limitWorkingProxyList(self, workingProxyList: list[dict]) -> list[dict]:
        if not self.proxyResultCountInt:
            return workingProxyList

        return workingProxyList[: self.proxyResultCountInt]

    def saveWorkingProxyList(self, workingProxyList: list[dict]) -> str:
        # Store reusable proxy values only; full ranking metadata is too long for KeyVal path writes.
        valueStr = self.buildSavedProxyValueStr(workingProxyList)
        if not valueStr:
            return ""

        return self.update(valueStr)

    def buildSavedProxyValueStr(self, workingProxyList: list[dict]) -> str:
        proxyValueList = []
        for workingProxyDict in workingProxyList:
            if len(proxyValueList) >= self.getMaxSavedProxyCountInt():
                break

            proxyStr = str(workingProxyDict.get("proxy") or "")
            if not proxyStr:
                continue

            candidateProxyValueList = [*proxyValueList, proxyStr]
            candidateValueStr = json.dumps(
                candidateProxyValueList,
                ensure_ascii=True,
                separators=(",", ":"),
            )
            if len(candidateValueStr) > KEY_VAL_MAX_VALUE_LENGTH_INT:
                if proxyValueList:
                    break
                continue

            proxyValueList = candidateProxyValueList

        if not proxyValueList:
            return ""

        return json.dumps(
            proxyValueList,
            ensure_ascii=True,
            separators=(",", ":"),
        )

    def onWorkingProxySaveFailure(self, error: Exception) -> None:
        return None

    def onWorkingProxySaveSkipped(self) -> None:
        return None

    def buildWorkingProxyRecord(
        self,
        proxyStr: str,
        timingMsList: list[int],
        lastCheckedAtStr: str,
    ) -> dict:
        successCountInt = len(timingMsList)
        averageTimingMsInt = int(round(sum(timingMsList) / successCountInt))
        return {
            "proxy": proxyStr,
            "averageTimingMs": averageTimingMsInt,
            "successCount": successCountInt,
            "lastCheckedAt": lastCheckedAtStr,
        }

    def getTimingMsInt(self, testResultDict: dict) -> int:
        timingMsValue = testResultDict.get("timingMs")
        if isinstance(timingMsValue, (int, float)):
            return max(0, int(round(timingMsValue)))

        return self.proxyMaxTimingMillisecondInt + 1

    def getKeyValProxyKey(self) -> str:
        return hashStringValue(self.keyValStoreProxyStr)

    def getKeyValDummyProxyKey(self) -> str:
        return self.getKeyValProxyKey()

    def getMaxSavedProxyCountInt(self) -> int:
        if self.proxyResultCountInt:
            return min(self.proxyResultCountInt, KEY_VAL_MAX_SAVED_PROXY_COUNT_INT)

        return KEY_VAL_MAX_SAVED_PROXY_COUNT_INT

    def normalizeProxySelectionMode(self, proxySelectionModeStr: str) -> str:
        normalizedProxySelectionModeStr = str(
            proxySelectionModeStr or DEFAULT_PROXY_SELECTION_MODE_STR,
        ).lower()
        if normalizedProxySelectionModeStr == PROXY_SELECTION_MODE_RANDOM_STR:
            return PROXY_SELECTION_MODE_RANDOM_STR

        return DEFAULT_PROXY_SELECTION_MODE_STR

    def getAvailableResource(self) -> dict | None:
        """Select a usable proxy/IP resource once business rules are implemented."""
        raise NotImplementedError("Elastic IP pool selection is not implemented yet.")

    def markResourceFailed(self, resourceIdStr: str) -> None:
        """Record a failed proxy/IP resource once business rules are implemented."""
        raise NotImplementedError("Elastic IP pool failure handling is not implemented yet.")
