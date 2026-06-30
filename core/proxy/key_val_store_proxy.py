import json
from http.client import HTTPException
from json import JSONDecodeError
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from core.constant.elastic_ip_pool_constant import (
    DEFAULT_TIMEOUT_SECOND_INT,
    KEY_VAL_API_BASE_URL_STR,
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
    ) -> None:
        self.baseUrlStr = baseUrlStr.rstrip("/")
        self.timeoutSecondInt = timeoutSecondInt

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

        valueStr = self._extractValueFromResponse(responseTextStr)

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

        responseValueStr = self._extractValueFromResponse(responseTextStr)

        return {
            "key": keyStr,
            "stored": 200 <= statusCodeInt < 300,
            "value": valueStr,
            "response_value": responseValueStr,
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
        request = Request(
            urlStr,
            method="GET",
            headers={
                "Accept": "application/json, text/plain",
                "User-Agent": KEY_VAL_USER_AGENT_STR,
            },
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
        if not responseTextStr:
            return None

        try:
            responseDict = json.loads(responseTextStr)
        except JSONDecodeError:
            return responseTextStr

        if not isinstance(responseDict, dict):
            return responseTextStr

        valueStr = responseDict.get("val")
        if valueStr is None:
            return responseTextStr

        return str(valueStr)
