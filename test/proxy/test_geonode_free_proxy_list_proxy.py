import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from n_elastic_ip_pool.proxy.geonode_free_proxy_list_proxy import (
    GeonodeFreeProxyListProxy,
    GeonodeFreeProxyListProxyError,
)


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


class GeonodeFreeProxyListProxyTest(unittest.TestCase):
    def testBuildFetchUrlUsesDefaultQueryParameter(self) -> None:
        resultStr = GeonodeFreeProxyListProxy().buildFetchUrl()

        self.assertEqual(
            resultStr,
            "https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&sort_by=lastChecked&sort_type=desc&protocols=http%2Chttps&anonymityLevel=elite&filterUpTime=80",
        )

    def testBuildFetchUrlAllowsOverride(self) -> None:
        geonodeFreeProxyListProxy = GeonodeFreeProxyListProxy(
            baseUrlStr="https://geonode.example.test/api/proxy-list",
            limitInt=25,
            pageInt=2,
            sortByStr="latency",
            sortTypeStr="asc",
            protocolsStr="http",
            anonymityLevelStr="anonymous",
            minUpTimeInt=50,
        )

        resultStr = geonodeFreeProxyListProxy.buildFetchUrl()

        self.assertEqual(
            resultStr,
            "https://geonode.example.test/api/proxy-list?limit=25&page=2&sort_by=latency&sort_type=asc&protocols=http&anonymityLevel=anonymous&filterUpTime=50",
        )

    def testParseProxyCandidateJsonNormalizesRecordsToCandidateText(self) -> None:
        responseTextStr = json.dumps(
            {
                "data": [
                    {
                        "ip": "203.0.113.10",
                        "port": "8080",
                        "protocols": ["http"],
                        "country": "US",
                        "anonymityLevel": "elite",
                        "upTime": "98.5",
                        "latency": 120.5,
                        "responseTime": 350,
                    },
                    {
                        "ip": "198.51.100.20",
                        "port": 3128,
                        "protocols": ["https"],
                    },
                ],
            },
        )

        resultDict = GeonodeFreeProxyListProxy().parseProxyCandidateJson(
            responseTextStr,
        )

        self.assertEqual(
            resultDict["proxy_candidate_text"],
            "203.0.113.10:8080\n198.51.100.20:3128\n",
        )
        self.assertEqual(
            resultDict["proxy_candidate_metadata_list"][0]["proxy"],
            "203.0.113.10:8080",
        )
        self.assertEqual(
            resultDict["proxy_candidate_metadata_list"][0]["protocols"],
            ["http"],
        )
        self.assertEqual(
            resultDict["proxy_candidate_metadata_list"][0]["upTime"],
            98.5,
        )

    def testParseProxyCandidateJsonSkipsRecordsMissingIpOrPort(self) -> None:
        responseTextStr = json.dumps(
            {
                "data": [
                    {"port": "8080", "protocols": ["http"]},
                    {"ip": "203.0.113.10", "protocols": ["http"]},
                    {"ip": "198.51.100.20", "port": "3128", "protocols": ["https"]},
                ],
            },
        )

        resultDict = GeonodeFreeProxyListProxy().parseProxyCandidateJson(
            responseTextStr,
        )

        self.assertEqual(resultDict["proxy_candidate_text"], "198.51.100.20:3128\n")

    def testParseProxyCandidateJsonSkipsUnsupportedProtocols(self) -> None:
        responseTextStr = json.dumps(
            {
                "data": [
                    {
                        "ip": "203.0.113.10",
                        "port": "1080",
                        "protocols": ["socks5"],
                    },
                    {
                        "ip": "198.51.100.20",
                        "port": "8080",
                        "protocols": ["http", "socks4"],
                    },
                ],
            },
        )

        resultDict = GeonodeFreeProxyListProxy(
            protocolsStr="http,https",
        ).parseProxyCandidateJson(responseTextStr)

        self.assertEqual(resultDict["proxy_candidate_text"], "198.51.100.20:8080\n")
        self.assertEqual(
            resultDict["proxy_candidate_metadata_list"][0]["protocols"],
            ["http"],
        )

    def testParseProxyCandidateJsonRaisesProviderErrorForMalformedJson(self) -> None:
        with self.assertRaises(GeonodeFreeProxyListProxyError):
            GeonodeFreeProxyListProxy().parseProxyCandidateJson("{broken-json")

    def testFetchProxyCandidateTextWrapsHttpErrors(self) -> None:
        httpError = HTTPError(
            url="https://proxylist.geonode.com/api/proxy-list",
            code=500,
            msg="server error",
            hdrs={},
            fp=None,
        )

        with patch(
            "n_elastic_ip_pool.proxy.geonode_free_proxy_list_proxy.urlopen",
            side_effect=httpError,
        ):
            with self.assertRaises(GeonodeFreeProxyListProxyError):
                GeonodeFreeProxyListProxy().fetchProxyCandidateText()
        httpError.close()

    def testFetchProxyCandidateTextReturnsNormalizedData(self) -> None:
        responseTextStr = json.dumps(
            {
                "data": [
                    {
                        "ip": "203.0.113.10",
                        "port": "8080",
                        "protocols": ["http"],
                    },
                ],
            },
        )

        with patch(
            "n_elastic_ip_pool.proxy.geonode_free_proxy_list_proxy.urlopen",
            return_value=FakeHttpResponse(responseTextStr, 200),
        ) as urlopenMock:
            resultDict = GeonodeFreeProxyListProxy(
                timeoutSecondInt=4,
            ).fetchProxyCandidateText()

        request = urlopenMock.call_args.args[0]
        self.assertEqual(request.get_method(), "GET")
        self.assertEqual(request.headers["Accept"], "application/json")
        self.assertEqual(urlopenMock.call_args.kwargs["timeout"], 4)
        self.assertEqual(resultDict["status_code"], 200)
        self.assertEqual(resultDict["proxy_candidate_text"], "203.0.113.10:8080\n")


if __name__ == "__main__":
    unittest.main()
