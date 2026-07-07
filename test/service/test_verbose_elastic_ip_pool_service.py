import unittest
from unittest.mock import patch

from n_elastic_ip_pool.constant.elastic_ip_pool_constant import LOGGER_LEVEL_ENV_NAME_STR
from n_elastic_ip_pool.helper.string_hash_helper import hashStringValue
from n_elastic_ip_pool.service.verbose_elastic_ip_pool_service import VerboseElasticIpPoolService


class FakeKeyValStoreProxy:
    def __init__(self, storedBool: bool = True) -> None:
        self.valueStr = ""
        self.getKeyStr = ""
        self.setKeyStr = ""
        self.setValueStr = ""
        self.storedBool = storedBool

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
            "stored": self.storedBool,
            "value": valueStr,
            "response_value": valueStr,
            "status_code": 200 if self.storedBool else 500,
        }

    def buildGetUrl(self, keyStr: str) -> str:
        return f"https://example.com/get/{keyStr}"

    def buildSetUrl(self, keyStr: str, valueStr: str) -> str:
        return f"https://example.com/set/{keyStr}/{valueStr}"


class FakeProxyScrapeProxy:
    def __init__(self) -> None:
        self.fetchCountInt = 0

    def buildFetchUrl(self) -> str:
        return "https://proxy.example.test/?request=getproxies"

    def fetchProxyCandidateText(self) -> dict:
        self.fetchCountInt += 1
        return {
            "url": "https://proxy.example.test",
            "status_code": 200,
            "proxy_candidate_text": "proxy-one.example.net:8080\n",
        }


class FakeGeonodeFreeProxyListProxy:
    def buildFetchUrl(self) -> str:
        return "https://geonode.example.test/api/proxy-list?limit=500"

    def fetchProxyCandidateText(self) -> dict:
        return {
            "url": "https://geonode.example.test",
            "status_code": 200,
            "proxy_candidate_text": "",
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
    def testRunDefaultsToInfoAndDoesNotSaveWhenNoneWork(self) -> None:
        keyValStoreProxy = FakeKeyValStoreProxy()
        service = VerboseElasticIpPoolService(
            keyValStoreProxyStr="custom-key-source",
            keyValStoreProxy=keyValStoreProxy,
            elasticIpHealthCheckProxy=FakeElasticIpHealthCheckProxy(),
            proxyScrapeProxy=FakeProxyScrapeProxy(),
            geonodeFreeProxyListProxy=FakeGeonodeFreeProxyListProxy(),
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
        self.assertIn("[proxyscrape] returned proxy rows: 1", printedTextStr)
        self.assertIn("[candidate] valid proxy count: 1", printedTextStr)
        self.assertNotIn("[candidate] 1/1: proxy-one.example.net:8080", printedTextStr)
        self.assertNotIn("[validation] testing proxy: proxy-one.example.net:8080", printedTextStr)
        self.assertIn("[cache] usable saved proxy: none", printedTextStr)
        self.assertRegex(printedTextStr, r"\[discovery\] took \d+\.\d{3} seconds")
        self.assertRegex(printedTextStr, r"\[run\] took \d+\.\d{3} seconds")

    def testRunInfoPrintsValidationPassSummaryWhenProxyKeepsWorking(self) -> None:
        keyValStoreProxy = FakeKeyValStoreProxy()
        service = VerboseElasticIpPoolService(
            keyValStoreProxyStr="custom-key-source",
            keyValStoreProxy=keyValStoreProxy,
            elasticIpHealthCheckProxy=FakeWorkingElasticIpHealthCheckProxy(),
            proxyScrapeProxy=FakeProxyScrapeProxy(),
            saveWorkingProxyBool=True,
        )

        with patch("builtins.print") as printMock:
            resultStr = service.run()

        printedTextStr = "\n".join(
            " ".join(str(arg) for arg in call.args)
            for call in printMock.call_args_list
        )
        self.assertEqual(resultStr, "proxy-one.example.net:8080")
        self.assertIn("[validation] first pass started", printedTextStr)
        self.assertIn("[validation] second pass started", printedTextStr)
        self.assertIn("[validation] third pass started", printedTextStr)
        self.assertIn(
            "[validation] first pass finished; passed=1",
            printedTextStr,
        )
        self.assertIn(
            "[validation] second pass finished; passed=1",
            printedTextStr,
        )
        self.assertIn(
            "[validation] third pass finished; passed=1",
            printedTextStr,
        )
        self.assertIn("[cache] stored proxy list:", printedTextStr)

    def testRunUsesWorkingSavedProxyWithoutDiscoveryOrSave(self) -> None:
        keyValStoreProxy = FakeKeyValStoreProxy()
        keyValStoreProxy.valueStr = '["saved-fast.example.net:8080"]'
        proxyScrapeProxy = FakeProxyScrapeProxy()
        service = VerboseElasticIpPoolService(
            keyValStoreProxyStr="custom-key-source",
            keyValStoreProxy=keyValStoreProxy,
            elasticIpHealthCheckProxy=FakeWorkingElasticIpHealthCheckProxy(),
            proxyScrapeProxy=proxyScrapeProxy,
        )

        with patch("builtins.print") as printMock:
            resultStr = service.run()

        printedTextStr = "\n".join(
            " ".join(str(arg) for arg in call.args)
            for call in printMock.call_args_list
        )
        self.assertEqual(resultStr, "saved-fast.example.net:8080")
        self.assertEqual(service.finalValueStr, "saved-fast.example.net:8080")
        self.assertEqual(service.rankedProxyList, ["saved-fast.example.net:8080"])
        self.assertEqual(proxyScrapeProxy.fetchCountInt, 0)
        self.assertEqual(keyValStoreProxy.setValueStr, "")
        self.assertIn(
            "[cache] usable saved proxy: [redacted-network-location]",
            printedTextStr,
        )
        self.assertNotIn("saved-fast.example.net:8080", printedTextStr)
        self.assertNotIn("[discovery] starting ProxyScrape search", printedTextStr)

    def testRunReturnsWorkingProxyWhenCacheSaveFails(self) -> None:
        keyValStoreProxy = FakeKeyValStoreProxy(storedBool=False)
        service = VerboseElasticIpPoolService(
            keyValStoreProxyStr="custom-key-source",
            keyValStoreProxy=keyValStoreProxy,
            elasticIpHealthCheckProxy=FakeWorkingElasticIpHealthCheckProxy(),
            proxyScrapeProxy=FakeProxyScrapeProxy(),
            saveWorkingProxyBool=True,
        )

        with patch("builtins.print") as printMock:
            resultStr = service.run()

        printedTextStr = "\n".join(
            " ".join(str(arg) for arg in call.args)
            for call in printMock.call_args_list
        )
        self.assertEqual(resultStr, "proxy-one.example.net:8080")
        self.assertIn("[cache] save skipped:", printedTextStr)
        self.assertIn("Proxy value was not stored in KeyVal.", printedTextStr)
        self.assertIn(
            "[run] selected proxy: [redacted-network-location]",
            printedTextStr,
        )
        self.assertNotIn("proxy-one.example.net:8080", printedTextStr)

    def testRunDebugPrintsDetailedCandidateAndProxyTestLines(self) -> None:
        keyValStoreProxy = FakeKeyValStoreProxy()
        service = VerboseElasticIpPoolService(
            keyValStoreProxyStr="custom-key-source",
            keyValStoreProxy=keyValStoreProxy,
            elasticIpHealthCheckProxy=FakeElasticIpHealthCheckProxy(),
            proxyScrapeProxy=FakeProxyScrapeProxy(),
            geonodeFreeProxyListProxy=FakeGeonodeFreeProxyListProxy(),
            loggerLevelStr="DEBUG",
        )

        with patch("builtins.print") as printMock:
            service.run()

        printedTextStr = "\n".join(
            " ".join(str(arg) for arg in call.args)
            for call in printMock.call_args_list
        )
        self.assertIn("[proxyscrape] request URL:", printedTextStr)
        self.assertIn("[candidate] 1/1: [redacted-network-location]", printedTextStr)
        self.assertIn("[validation] testing proxy: [redacted-network-location]", printedTextStr)
        self.assertIn("[validation] result:", printedTextStr)
        self.assertNotIn("proxy-one.example.net:8080", printedTextStr)

    def testRunUsesLoggerEnvironmentValue(self) -> None:
        keyValStoreProxy = FakeKeyValStoreProxy()

        with patch.dict("os.environ", {LOGGER_LEVEL_ENV_NAME_STR: "debug"}):
            service = VerboseElasticIpPoolService(
                keyValStoreProxyStr="custom-key-source",
                keyValStoreProxy=keyValStoreProxy,
                elasticIpHealthCheckProxy=FakeElasticIpHealthCheckProxy(),
                proxyScrapeProxy=FakeProxyScrapeProxy(),
                geonodeFreeProxyListProxy=FakeGeonodeFreeProxyListProxy(),
            )

        with patch("builtins.print") as printMock:
            service.run()

        printedTextStr = "\n".join(
            " ".join(str(arg) for arg in call.args)
            for call in printMock.call_args_list
        )
        self.assertIn("[run] log level: DEBUG", printedTextStr)
        self.assertIn("[validation] testing proxy: [redacted-network-location]", printedTextStr)
        self.assertNotIn("proxy-one.example.net:8080", printedTextStr)

    def testRunFallsBackToInfoForInvalidLoggerEnvironmentValue(self) -> None:
        keyValStoreProxy = FakeKeyValStoreProxy()

        with patch.dict("os.environ", {LOGGER_LEVEL_ENV_NAME_STR: "trace"}):
            service = VerboseElasticIpPoolService(
                keyValStoreProxyStr="custom-key-source",
                keyValStoreProxy=keyValStoreProxy,
                elasticIpHealthCheckProxy=FakeElasticIpHealthCheckProxy(),
                proxyScrapeProxy=FakeProxyScrapeProxy(),
                geonodeFreeProxyListProxy=FakeGeonodeFreeProxyListProxy(),
            )

        with patch("builtins.print") as printMock:
            service.run()

        printedTextStr = "\n".join(
            " ".join(str(arg) for arg in call.args)
            for call in printMock.call_args_list
        )
        self.assertIn("[run] log level: INFO", printedTextStr)
        self.assertNotIn("[validation] testing proxy: proxy-one.example.net:8080", printedTextStr)


if __name__ == "__main__":
    unittest.main()
