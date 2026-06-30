import time
from datetime import UTC, datetime
from http.client import HTTPException
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener

from core.constant.elastic_ip_pool_constant import (
    PROXY_MAX_TIMING_MILLISECOND_INT,
    PROXY_TEST_TARGET_URL_STR,
    PROXY_TEST_USER_AGENT_STR,
)
from core.helper.proxy_address_format_helper import normalizeProxyAddress


class ElasticIpHealthCheckProxy:
    """External connectivity check abstraction for candidate proxy resources."""

    def __init__(
        self,
        targetUrlStr: str = PROXY_TEST_TARGET_URL_STR,
        timeoutSecondInt: int | None = None,
        timeoutMillisecondInt: int = PROXY_MAX_TIMING_MILLISECOND_INT,
    ) -> None:
        self.targetUrlStr = targetUrlStr
        self.timeoutSecondFloat = (
            float(timeoutSecondInt)
            if timeoutSecondInt is not None
            else max(1, timeoutMillisecondInt) / 1000
        )

    def checkHealth(self, proxyResourceDict: dict) -> dict:
        """Check a proxy resource dictionary using its proxy or ip_address value."""
        proxyStr = str(
            proxyResourceDict.get("proxy")
            or proxyResourceDict.get("ip_address")
            or "",
        )
        return self.testProxy(proxyStr)

    def testProxy(self, proxyStr: str) -> dict:
        """Test whether a candidate proxy can reach the configured target URL."""
        checkedAtStr = self._getCheckedAtStr()
        normalizedProxyStr = normalizeProxyAddress(proxyStr)
        if not normalizedProxyStr:
            return self._buildResult(
                proxyStr=str(proxyStr),
                isWorkingBool=False,
                timingMsInt=None,
                checkedAtStr=checkedAtStr,
                errorStr="invalid_proxy_format",
                statusCodeInt=None,
            )

        request = Request(
            self.targetUrlStr,
            method="GET",
            headers={
                "Accept": "application/json, text/plain, */*",
                "User-Agent": PROXY_TEST_USER_AGENT_STR,
            },
        )
        proxyUrlStr = f"http://{normalizedProxyStr}"
        opener = build_opener(
            ProxyHandler(
                {
                    "http": proxyUrlStr,
                    "https": proxyUrlStr,
                },
            ),
        )

        startFloat = time.perf_counter()
        try:
            with opener.open(request, timeout=self.timeoutSecondFloat) as response:
                response.read(512)
                statusCodeInt = response.getcode()
        except HTTPError as error:
            return self._buildResult(
                proxyStr=normalizedProxyStr,
                isWorkingBool=False,
                timingMsInt=self._getTimingMsInt(startFloat),
                checkedAtStr=checkedAtStr,
                errorStr=f"http_status_{error.code}",
                statusCodeInt=error.code,
            )
        except (HTTPException, TimeoutError, URLError, OSError, ValueError) as error:
            return self._buildResult(
                proxyStr=normalizedProxyStr,
                isWorkingBool=False,
                timingMsInt=self._getTimingMsInt(startFloat),
                checkedAtStr=checkedAtStr,
                errorStr=error.__class__.__name__,
                statusCodeInt=None,
            )

        if statusCodeInt < 200 or statusCodeInt >= 400:
            return self._buildResult(
                proxyStr=normalizedProxyStr,
                isWorkingBool=False,
                timingMsInt=self._getTimingMsInt(startFloat),
                checkedAtStr=checkedAtStr,
                errorStr="unexpected_status_code",
                statusCodeInt=statusCodeInt,
            )

        return self._buildResult(
            proxyStr=normalizedProxyStr,
            isWorkingBool=True,
            timingMsInt=self._getTimingMsInt(startFloat),
            checkedAtStr=checkedAtStr,
            errorStr=None,
            statusCodeInt=statusCodeInt,
        )

    def _buildResult(
        self,
        proxyStr: str,
        isWorkingBool: bool,
        timingMsInt: int | None,
        checkedAtStr: str,
        errorStr: str | None,
        statusCodeInt: int | None,
    ) -> dict:
        return {
            "proxy": proxyStr,
            "isWorking": isWorkingBool,
            "timingMs": timingMsInt,
            "checkedAt": checkedAtStr,
            "error": errorStr,
            "statusCode": statusCodeInt,
        }

    def _getCheckedAtStr(self) -> str:
        return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    def _getTimingMsInt(self, startFloat: float) -> int:
        return max(0, int(round((time.perf_counter() - startFloat) * 1000)))
