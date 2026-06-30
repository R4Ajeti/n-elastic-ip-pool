import unittest
from unittest.mock import patch

from core.helper.string_hash_helper import hashStringValue
from core.service.verbose_elastic_ip_pool_service import VerboseElasticIpPoolService


class FakeKeyValStoreProxy:
    def __init__(self) -> None:
        self.valueStr = ""
        self.getKeyStr = ""
        self.setKeyStr = ""
        self.setValueStr = ""

    def getValue(self, keyStr: str) -> dict:
        self.getKeyStr = keyStr
        return {
            "key": keyStr,
            "exists": bool(self.valueStr),
            "value": self.valueStr or None,
            "status_code": 200,
        }

    def setValue(self, keyStr: str, valueStr: str) -> dict:
        self.setKeyStr = keyStr
        self.setValueStr = valueStr
        self.valueStr = valueStr
        return {
            "key": keyStr,
            "stored": True,
            "value": valueStr,
            "response_value": valueStr,
            "status_code": 200,
        }

    def buildGetUrl(self, keyStr: str) -> str:
        return f"https://example.com/get/{keyStr}"

    def buildSetUrl(self, keyStr: str, valueStr: str) -> str:
        return f"https://example.com/set/{keyStr}/{valueStr}"


class FakeProxyScrapeProxy:
    def buildFetchUrl(self) -> str:
        return "https://proxy.example.test/?request=getproxies"

    def fetchProxyCandidateText(self) -> dict:
        return {
            "url": "https://proxy.example.test",
            "status_code": 200,
            "proxy_candidate_text": "proxy-one.example.net:8080\n",
        }


class FakeElasticIpHealthCheckProxy:
    def testProxy(self, proxyStr: str) -> dict:
        return {
            "proxy": proxyStr,
            "isWorking": False,
            "timingMs": None,
            "checkedAt": "2026-01-01T00:00:00Z",
            "error": "not_used",
            "statusCode": None,
        }


class FakeWorkingElasticIpHealthCheckProxy:
    def testProxy(self, proxyStr: str) -> dict:
        return {
            "proxy": proxyStr,
            "isWorking": True,
            "timingMs": 50,
            "checkedAt": "2026-01-01T00:00:00Z",
            "error": None,
            "statusCode": 200,
        }


class VerboseElasticIpPoolServiceTest(unittest.TestCase):
    def testRunUsesConstructorKeySourceAndStoresEmptyProxyListWhenNoneWork(self) -> None:
        keyValStoreProxy = FakeKeyValStoreProxy()
        service = VerboseElasticIpPoolService(
            keyValStoreProxyStr="custom-key-source",
            keyValStoreProxy=keyValStoreProxy,
            elasticIpHealthCheckProxy=FakeElasticIpHealthCheckProxy(),
            proxyScrapeProxy=FakeProxyScrapeProxy(),
        )
        expectedKeyStr = hashStringValue("custom-key-source")

        with patch("builtins.print") as printMock:
            resultStr = service.run()

        self.assertIsNone(resultStr)
        self.assertEqual(keyValStoreProxy.setKeyStr, "")
        self.assertEqual(keyValStoreProxy.getKeyStr, expectedKeyStr)
        self.assertEqual(keyValStoreProxy.setValueStr, "")
        printedTextStr = "\n".join(
            " ".join(str(arg) for arg in call.args)
            for call in printMock.call_args_list
        )
        self.assertIn("[proxy_scrape.fetch] raw proxy 1: proxy-one.example.net:8080", printedTextStr)
        self.assertIn("[service.parseProxyCandidateList] valid proxy 1: proxy-one.example.net:8080", printedTextStr)
        self.assertIn("[service.testProxy] testing proxy: proxy-one.example.net:8080", printedTextStr)
        self.assertRegex(printedTextStr, r"\[service\.search\] took \d+\.\d{3} seconds")
        self.assertRegex(printedTextStr, r"\[manual\.run\] took \d+\.\d{3} seconds")

    def testRunPrintsValidationPassStartsWhenProxyKeepsWorking(self) -> None:
        keyValStoreProxy = FakeKeyValStoreProxy()
        service = VerboseElasticIpPoolService(
            keyValStoreProxyStr="custom-key-source",
            keyValStoreProxy=keyValStoreProxy,
            elasticIpHealthCheckProxy=FakeWorkingElasticIpHealthCheckProxy(),
            proxyScrapeProxy=FakeProxyScrapeProxy(),
        )

        with patch("builtins.print") as printMock:
            resultStr = service.run()

        printedTextStr = "\n".join(
            " ".join(str(arg) for arg in call.args)
            for call in printMock.call_args_list
        )
        self.assertEqual(resultStr, "proxy-one.example.net:8080")
        self.assertIn("[service.validateProxyCandidateList] start first pass", printedTextStr)
        self.assertIn("[service.validateProxyCandidateList] start second pass", printedTextStr)
        self.assertIn("[service.validateProxyCandidateList] start third pass", printedTextStr)
        self.assertIn(
            "[service.validateProxyCandidateList] finish first pass; passed proxy count: 1",
            printedTextStr,
        )
        self.assertIn(
            "[service.validateProxyCandidateList] finish second pass; passed proxy count: 1",
            printedTextStr,
        )
        self.assertIn(
            "[service.validateProxyCandidateList] finish third pass; passed proxy count: 1",
            printedTextStr,
        )


if __name__ == "__main__":
    unittest.main()
