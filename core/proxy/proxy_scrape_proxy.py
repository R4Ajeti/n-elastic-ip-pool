from http.client import HTTPException
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from core.constant.elastic_ip_pool_constant import (
    DEFAULT_TIMEOUT_SECOND_INT,
    PROXY_SCRAPE_ANONYMITY_FILTER_STR,
    PROXY_SCRAPE_API_BASE_URL_STR,
    PROXY_SCRAPE_COUNTRY_FILTER_STR,
    PROXY_SCRAPE_PROXY_TYPE_STR,
    PROXY_SCRAPE_REQUEST_VALUE_STR,
    PROXY_SCRAPE_SSL_FILTER_STR,
    PROXY_SCRAPE_TIMEOUT_MILLISECOND_INT,
    PROXY_TEST_USER_AGENT_STR,
)


class ProxyScrapeProxyError(RuntimeError):
    """Raised when the ProxyScrape provider request fails."""


class ProxyScrapeProxy:
    """External ProxyScrape API abstraction."""

    def __init__(
        self,
        baseUrlStr: str = PROXY_SCRAPE_API_BASE_URL_STR,
        requestValueStr: str = PROXY_SCRAPE_REQUEST_VALUE_STR,
        proxyTypeStr: str = PROXY_SCRAPE_PROXY_TYPE_STR,
        timeoutMillisecondInt: int = PROXY_SCRAPE_TIMEOUT_MILLISECOND_INT,
        countryFilterStr: str = PROXY_SCRAPE_COUNTRY_FILTER_STR,
        sslFilterStr: str = PROXY_SCRAPE_SSL_FILTER_STR,
        anonymityFilterStr: str = PROXY_SCRAPE_ANONYMITY_FILTER_STR,
        timeoutSecondInt: int = DEFAULT_TIMEOUT_SECOND_INT,
    ) -> None:
        self.baseUrlStr = baseUrlStr.rstrip("/")
        self.requestValueStr = requestValueStr
        self.proxyTypeStr = proxyTypeStr
        self.timeoutMillisecondInt = timeoutMillisecondInt
        self.countryFilterStr = countryFilterStr
        self.sslFilterStr = sslFilterStr
        self.anonymityFilterStr = anonymityFilterStr
        self.timeoutSecondInt = timeoutSecondInt

    def fetchProxyCandidateText(self) -> dict:
        """Fetch the provider response and return normalized internal data."""
        urlStr = self.buildFetchUrl()
        request = Request(
            urlStr,
            method="GET",
            headers={
                "Accept": "text/plain",
                "User-Agent": PROXY_TEST_USER_AGENT_STR,
            },
        )

        try:
            with urlopen(request, timeout=self.timeoutSecondInt) as response:
                responseTextStr = response.read().decode("utf-8")
                statusCodeInt = response.getcode()
        except HTTPError as error:
            raise ProxyScrapeProxyError(
                f"ProxyScrape request failed with status {error.code}.",
            ) from error
        except (HTTPException, TimeoutError, URLError, OSError) as error:
            raise ProxyScrapeProxyError("ProxyScrape request failed.") from error

        return {
            "url": urlStr,
            "status_code": statusCodeInt,
            "proxy_candidate_text": responseTextStr,
        }

    def buildFetchUrl(self) -> str:
        queryParamStr = urlencode(
            [
                ("request", self.requestValueStr),
                ("proxytype", self.proxyTypeStr),
                ("timeout", str(self.timeoutMillisecondInt)),
                ("country", self.countryFilterStr),
                ("ssl", self.sslFilterStr),
                ("anonymity", self.anonymityFilterStr),
            ],
        )
        return f"{self.baseUrlStr}/?{queryParamStr}"
