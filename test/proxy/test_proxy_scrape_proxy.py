import unittest
from unittest.mock import patch

from n_elastic_ip_pool.proxy.proxy_scrape_proxy import ProxyScrapeProxy


class FakeHttpResponse:
    def __init__(self, responseTextStr: str, statusCodeInt: int = 200) -> None:
        self.responseTextStr = responseTextStr
        self.statusCodeInt = statusCodeInt

    def __enter__(self) -> "FakeHttpResponse":
        return self

    def __exit__(self, excType, excValue, traceback) -> None:
        return None

    def read(self) -> bytes:
        return self.responseTextStr.encode("utf-8")

    def getcode(self) -> int:
        return self.statusCodeInt


class ProxyScrapeProxyTest(unittest.TestCase):
    def testBuildFetchUrlUsesDefaultQueryParameter(self) -> None:
        resultStr = ProxyScrapeProxy().buildFetchUrl()

        self.assertEqual(
            resultStr,
            "https://api.proxyscrape.com/?request=getproxies&proxytype=all&timeout=300&country=all&ssl=yes&anonymity=elite",
        )

    def testBuildFetchUrlAllowsOverride(self) -> None:
        proxyScrapeProxy = ProxyScrapeProxy(
            baseUrlStr="https://proxy.example.test",
            requestValueStr="displayproxies",
            proxyTypeStr="http",
            timeoutMillisecondInt=500,
            countryFilterStr="US",
            sslFilterStr="no",
            anonymityFilterStr="anonymous",
        )

        resultStr = proxyScrapeProxy.buildFetchUrl()

        self.assertEqual(
            resultStr,
            "https://proxy.example.test/?request=displayproxies&proxytype=http&timeout=500&country=US&ssl=no&anonymity=anonymous",
        )

    def testFetchProxyCandidateTextReturnsNormalizedData(self) -> None:
        with patch(
            "n_elastic_ip_pool.proxy.proxy_scrape_proxy.urlopen",
            return_value=FakeHttpResponse("proxy-one.example.net:8080\n", 200),
        ) as urlopenMock:
            resultDict = ProxyScrapeProxy(timeoutSecondInt=4).fetchProxyCandidateText()

        request = urlopenMock.call_args.args[0]
        self.assertEqual(request.get_method(), "GET")
        self.assertEqual(urlopenMock.call_args.kwargs["timeout"], 4)
        self.assertEqual(resultDict["status_code"], 200)
        self.assertEqual(resultDict["proxy_candidate_text"], "proxy-one.example.net:8080\n")


if __name__ == "__main__":
    unittest.main()
