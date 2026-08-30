import json
from http.client import HTTPException
from json import JSONDecodeError
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from n_elastic_ip_pool.constant.elastic_ip_pool_constant import (
    DEFAULT_TIMEOUT_SECOND_INT,
    KEY_VAL_API_BASE_URL_STR,
    KEY_VAL_MISSING_KEY_STATUS_STR,
    KEY_VAL_USER_AGENT_STR,
)


class KeyValStoreProxyError(RuntimeError):
    """Raised when the KeyVal provider request cannot be normalized."""


class KeyValStoreProxy:
    """External key/value store proxy abstraction for KeyVal."""

    def __init__(
        self,
        baseUrlStr: str = KEY_VAL_API_BASE_URL_STR,
        timeoutSecondInt: int = DEFAULT_TIMEOUT_SECOND_INT,
        authTokenStr: str = "",
    ) -> None:
        self.baseUrlStr = baseUrlStr.rstrip("/")
        self.timeoutSecondInt = timeoutSecondInt
        self.authTokenStr = str(authTokenStr or "").strip()

    def getValue(self, keyStr: str) -> dict:
        """Read a value from KeyVal and return normalized internal data."""
        try:
            responseTextStr, statusCodeInt = self._sendGetRequest(
                self.buildGetUrl(keyStr),
            )
        except HTTPError as error:
            if error.code == 404:
                return {
                    "key": keyStr,
                    "exists": False,
                    "value": None,
                    "status_code": error.code,
                }

            raise KeyValStoreProxyError(
                f"KeyVal get request failed with status {error.code}.",
            ) from error

        valueStr, responseStatusStr = self._extractValueAndStatusFromResponse(responseTextStr)
        if responseStatusStr == KEY_VAL_MISSING_KEY_STATUS_STR:
            return {"key": keyStr, "exists": False, "value": None, "status_code": statusCodeInt}
        if responseStatusStr and responseStatusStr != "SUCCESS":
            raise KeyValStoreProxyError("KeyVal get request returned a provider error.")

        return {
            "key": keyStr,
            "exists": bool(valueStr),
            "value": valueStr,
            "status_code": statusCodeInt,
        }

    def setValue(self, keyStr: str, valueStr: str) -> dict:
        """Store a value in KeyVal and return normalized internal data."""
        try:
            responseTextStr, statusCodeInt = self._sendGetRequest(
                self.buildSetUrl(keyStr, valueStr),
            )
        except HTTPError as error:
            raise KeyValStoreProxyError(
                f"KeyVal set request failed with status {error.code}.",
            ) from error

        responseValueStr, responseStatusStr = self._extractValueAndStatusFromResponse(
            responseTextStr,
        )
        storedBool = 200 <= statusCodeInt < 300
        if responseStatusStr:
            storedBool = storedBool and responseStatusStr == "SUCCESS"

        return {
            "key": keyStr,
            "stored": storedBool,
            "value": valueStr,
            "response_value": responseValueStr,
            "response_status": responseStatusStr,
            "status_code": statusCodeInt,
        }

    def buildGetUrl(self, keyStr: str) -> str:
        encodedKeyStr = quote(keyStr, safe="")
        return f"{self.baseUrlStr}/get/{encodedKeyStr}"

    def buildSetUrl(self, keyStr: str, valueStr: str) -> str:
        encodedKeyStr = quote(keyStr, safe="")
        encodedValueStr = quote(valueStr, safe="")
        return f"{self.baseUrlStr}/set/{encodedKeyStr}/{encodedValueStr}"

    def _sendGetRequest(self, urlStr: str) -> tuple[str, int]:
        headerDict = {
            "Accept": "application/json, text/plain",
            "User-Agent": KEY_VAL_USER_AGENT_STR,
        }
        if self.authTokenStr:
            headerDict["Authorization"] = f"Bearer {self.authTokenStr}"

        request = Request(
            urlStr,
            method="GET",
            headers=headerDict,
        )

        try:
            with urlopen(request, timeout=self.timeoutSecondInt) as response:
                responseTextStr = response.read().decode("utf-8")
                statusCodeInt = response.getcode()
        except HTTPError:
            raise
        except (HTTPException, TimeoutError, URLError, OSError) as error:
            raise KeyValStoreProxyError("KeyVal request failed.") from error

        return responseTextStr, statusCodeInt

    def _extractValueFromResponse(self, responseTextStr: str) -> str | None:
        valueStr, _ = self._extractValueAndStatusFromResponse(responseTextStr)
        return valueStr

    def _extractStatusFromResponse(self, responseTextStr: str) -> str | None:
        _, statusStr = self._extractValueAndStatusFromResponse(responseTextStr)
        return statusStr

    def _extractValueAndStatusFromResponse(
        self,
        responseTextStr: str,
    ) -> tuple[str | None, str | None]:
        if not responseTextStr:
            return None, None

        responseDict = self._extractDictFromResponse(responseTextStr)
        if not isinstance(responseDict, dict):
            return responseTextStr, None

        valueStr = responseDict.get("val")
        statusStr = responseDict.get("status")
        if "val" in responseDict and valueStr is None:
            return None, None if statusStr is None else str(statusStr)
        return (
            responseTextStr if valueStr is None else str(valueStr),
            None if statusStr is None else str(statusStr),
        )

    def _extractDictFromResponse(self, responseTextStr: str) -> dict | None:
        try:
            responseDict = json.loads(responseTextStr)
        except JSONDecodeError:
            return None

        if not isinstance(responseDict, dict):
            return None

        return responseDict
