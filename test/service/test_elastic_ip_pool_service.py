import json
import unittest

from core.constant.elastic_ip_pool_constant import (
    KEY_VAL_DUMMY_PROXY_KEY_STR,
    KEY_VAL_DUMMY_PROXY_VALUE_STR,
)
from core.helper.string_hash_helper import hashStringValue
from core.proxy.elastic_ip_health_check_proxy import ElasticIpHealthCheckProxy
from core.proxy.key_val_store_proxy import KeyValStoreProxy
from core.proxy.proxy_scrape_proxy import ProxyScrapeProxyError
from core.repo.elastic_ip_pool_repo import ElasticIpPoolRepo
from core.service.elastic_ip_pool_service import ElasticIpPoolService


def buildTestResult(
    proxyStr: str,
    isWorkingBool: bool,
    timingMsInt: int | None = 100,
    errorStr: str | None = None,
) -> dict:
    return {
        "proxy": proxyStr,
        "isWorking": isWorkingBool,
        "timingMs": timingMsInt,
        "checkedAt": "2026-01-01T00:00:00Z",
        "error": errorStr,
        "statusCode": 200 if isWorkingBool else None,
    }


class FakeKeyValStoreProxy:
    def __init__(
        self,
        getResultDict: dict | None = None,
        storedBool: bool = True,
    ) -> None:
        self.getResultDict = getResultDict or {
            "key": "",
            "exists": False,
            "value": None,
            "status_code": 404,
        }
        self.storedBool = storedBool
        self.getKeyStr = ""
        self.setKeyStr = ""
        self.setValueStr = ""
        self.setValueCallCountInt = 0

    def getValue(self, keyStr: str) -> dict:
        self.getKeyStr = keyStr
        return self.getResultDict

    def setValue(self, keyStr: str, valueStr: str) -> dict:
        self.setKeyStr = keyStr
        self.setValueStr = valueStr
        self.setValueCallCountInt += 1
        return {
            "key": keyStr,
            "stored": self.storedBool,
            "value": valueStr,
            "response_value": valueStr,
            "status_code": 200 if self.storedBool else 500,
        }


class FakeProxyScrapeProxy:
    def __init__(
        self,
        responseTextStr: str = "",
        statusCodeInt: int = 200,
        error: Exception | None = None,
    ) -> None:
        self.responseTextStr = responseTextStr
        self.statusCodeInt = statusCodeInt
        self.error = error
        self.fetchCallCountInt = 0

    def fetchProxyCandidateText(self) -> dict:
        self.fetchCallCountInt += 1
        if self.error:
            raise self.error

        return {
            "url": "https://proxy.example.test",
            "status_code": self.statusCodeInt,
            "proxy_candidate_text": self.responseTextStr,
        }


class FakeElasticIpHealthCheckProxy:
    def __init__(self, resultListByProxy: dict[str, list[dict]]) -> None:
        self.resultListByProxy = {
            proxyStr: list(resultList)
            for proxyStr, resultList in resultListByProxy.items()
        }
        self.testCallList = []

    def testProxy(self, proxyStr: str) -> dict:
        self.testCallList.append(proxyStr)
        resultList = self.resultListByProxy.get(proxyStr, [])
        if not resultList:
            return buildTestResult(proxyStr, False, None, "missing_mock")

        return resultList.pop(0)


class ElasticIpPoolServiceTest(unittest.TestCase):
    def testGetReturnsSavedWorkingProxyFromKeyVal(self) -> None:
        expectedKeyStr = hashStringValue(KEY_VAL_DUMMY_PROXY_KEY_STR)
        savedValueStr = json.dumps(
            [
                {
                    "proxy": "proxy-slow.example.net:8080",
                    "averageTimingMs": 300,
                    "successCount": 3,
                    "lastCheckedAt": "2026-01-01T00:00:00Z",
                },
                {
                    "proxy": "proxy-fast.example.net:8080",
                    "averageTimingMs": 120,
                    "successCount": 3,
                    "lastCheckedAt": "2026-01-01T00:00:00Z",
                },
            ],
        )
        keyValStoreProxy = FakeKeyValStoreProxy(
            {
                "key": expectedKeyStr,
                "exists": True,
                "value": savedValueStr,
                "status_code": 200,
            },
        )
        healthCheckProxy = FakeElasticIpHealthCheckProxy(
            {
                "proxy-slow.example.net:8080": [
                    buildTestResult("proxy-slow.example.net:8080", True, 300),
                ],
                "proxy-fast.example.net:8080": [
                    buildTestResult("proxy-fast.example.net:8080", True, 80),
                ],
            },
        )
        proxyScrapeProxy = FakeProxyScrapeProxy("proxy-new.example.net:8080\n")
        service = ElasticIpPoolService(
            elasticIpHealthCheckProxy=healthCheckProxy,
            keyValStoreProxy=keyValStoreProxy,
            proxyScrapeProxy=proxyScrapeProxy,
        )

        resultStr = service.get()

        self.assertEqual(resultStr, "proxy-fast.example.net:8080")
        self.assertEqual(keyValStoreProxy.getKeyStr, expectedKeyStr)
        self.assertEqual(keyValStoreProxy.setValueCallCountInt, 0)
        self.assertEqual(proxyScrapeProxy.fetchCallCountInt, 0)

    def testGetIgnoresSavedProxyThatFailsValidation(self) -> None:
        savedValueStr = json.dumps(
            [
                {
                    "proxy": "proxy-old.example.net:8080",
                    "averageTimingMs": 100,
                    "successCount": 3,
                    "lastCheckedAt": "2026-01-01T00:00:00Z",
                },
            ],
        )
        keyValStoreProxy = FakeKeyValStoreProxy(
            {"key": "stored-key", "exists": True, "value": savedValueStr},
        )
        healthCheckProxy = FakeElasticIpHealthCheckProxy(
            {
                "proxy-old.example.net:8080": [
                    buildTestResult("proxy-old.example.net:8080", False, None, "timeout"),
                ],
                "proxy-new.example.net:8080": [
                    buildTestResult("proxy-new.example.net:8080", True, 140),
                    buildTestResult("proxy-new.example.net:8080", True, 130),
                    buildTestResult("proxy-new.example.net:8080", True, 120),
                ],
            },
        )
        service = ElasticIpPoolService(
            elasticIpHealthCheckProxy=healthCheckProxy,
            keyValStoreProxy=keyValStoreProxy,
            proxyScrapeProxy=FakeProxyScrapeProxy("proxy-new.example.net:8080\n"),
        )

        resultStr = service.get()

        self.assertEqual(resultStr, "proxy-new.example.net:8080")
        self.assertEqual(keyValStoreProxy.setValueCallCountInt, 1)

    def testGetCallsSearchWhenKeyValHasNoSavedProxy(self) -> None:
        proxyScrapeProxy = FakeProxyScrapeProxy("proxy-new.example.net:8080\n")
        service = ElasticIpPoolService(
            elasticIpHealthCheckProxy=FakeElasticIpHealthCheckProxy(
                {
                    "proxy-new.example.net:8080": [
                        buildTestResult("proxy-new.example.net:8080", True, 90),
                        buildTestResult("proxy-new.example.net:8080", True, 95),
                        buildTestResult("proxy-new.example.net:8080", True, 85),
                    ],
                },
            ),
            keyValStoreProxy=FakeKeyValStoreProxy(),
            proxyScrapeProxy=proxyScrapeProxy,
        )

        resultStr = service.get()

        self.assertEqual(resultStr, "proxy-new.example.net:8080")
        self.assertEqual(proxyScrapeProxy.fetchCallCountInt, 1)

    def testSearchFetchesProxiesFromProxyScrape(self) -> None:
        proxyScrapeProxy = FakeProxyScrapeProxy("proxy-new.example.net:8080\n")
        service = ElasticIpPoolService(
            elasticIpHealthCheckProxy=FakeElasticIpHealthCheckProxy(
                {
                    "proxy-new.example.net:8080": [
                        buildTestResult("proxy-new.example.net:8080", True, 90),
                        buildTestResult("proxy-new.example.net:8080", True, 90),
                        buildTestResult("proxy-new.example.net:8080", True, 90),
                    ],
                },
            ),
            keyValStoreProxy=FakeKeyValStoreProxy(),
            proxyScrapeProxy=proxyScrapeProxy,
        )

        service.search()

        self.assertEqual(proxyScrapeProxy.fetchCallCountInt, 1)

    def testParseProxyCandidateListRemovesDuplicates(self) -> None:
        service = ElasticIpPoolService(
            elasticIpHealthCheckProxy=FakeElasticIpHealthCheckProxy({}),
            keyValStoreProxy=FakeKeyValStoreProxy(),
            proxyScrapeProxy=FakeProxyScrapeProxy(),
        )

        resultList = service.parseProxyCandidateList(
            "proxy-one.example.net:8080\nproxy-one.example.net:8080\n",
        )

        self.assertEqual(resultList, ["proxy-one.example.net:8080"])

    def testParseProxyCandidateListIgnoresMalformedRows(self) -> None:
        service = ElasticIpPoolService(
            elasticIpHealthCheckProxy=FakeElasticIpHealthCheckProxy({}),
            keyValStoreProxy=FakeKeyValStoreProxy(),
            proxyScrapeProxy=FakeProxyScrapeProxy(),
        )

        resultList = service.parseProxyCandidateList(
            "not-a-proxy\nproxy-one.example.net:8080\nproxy-two.example.net:99999\n",
        )

        self.assertEqual(resultList, ["proxy-one.example.net:8080"])

    def testValidateProxyCandidateListTestsEveryProxyOnceBeforeRetesting(self) -> None:
        healthCheckProxy = FakeElasticIpHealthCheckProxy(
            {
                "proxy-one.example.net:8080": [
                    buildTestResult("proxy-one.example.net:8080", True, 100),
                    buildTestResult("proxy-one.example.net:8080", True, 100),
                    buildTestResult("proxy-one.example.net:8080", True, 100),
                ],
                "proxy-two.example.net:8080": [
                    buildTestResult("proxy-two.example.net:8080", True, 100),
                    buildTestResult("proxy-two.example.net:8080", True, 100),
                    buildTestResult("proxy-two.example.net:8080", True, 100),
                ],
            },
        )
        service = ElasticIpPoolService(
            elasticIpHealthCheckProxy=healthCheckProxy,
            keyValStoreProxy=FakeKeyValStoreProxy(),
            proxyScrapeProxy=FakeProxyScrapeProxy(),
        )

        service.validateProxyCandidateList(
            ["proxy-one.example.net:8080", "proxy-two.example.net:8080"],
        )

        self.assertEqual(
            healthCheckProxy.testCallList[:2],
            ["proxy-one.example.net:8080", "proxy-two.example.net:8080"],
        )

    def testSearchSavesOnlyProxiesWithThreeSuccessfulChecks(self) -> None:
        keyValStoreProxy = FakeKeyValStoreProxy()
        service = ElasticIpPoolService(
            elasticIpHealthCheckProxy=FakeElasticIpHealthCheckProxy(
                {
                    "proxy-one.example.net:8080": [
                        buildTestResult("proxy-one.example.net:8080", True, 100),
                        buildTestResult("proxy-one.example.net:8080", True, 100),
                        buildTestResult("proxy-one.example.net:8080", False, None, "timeout"),
                    ],
                    "proxy-two.example.net:8080": [
                        buildTestResult("proxy-two.example.net:8080", True, 120),
                        buildTestResult("proxy-two.example.net:8080", True, 110),
                        buildTestResult("proxy-two.example.net:8080", True, 100),
                    ],
                },
            ),
            keyValStoreProxy=keyValStoreProxy,
            proxyScrapeProxy=FakeProxyScrapeProxy(
                "proxy-one.example.net:8080\nproxy-two.example.net:8080\n",
            ),
        )

        resultStr = service.search()
        savedList = json.loads(keyValStoreProxy.setValueStr)

        self.assertEqual(resultStr, "proxy-two.example.net:8080")
        self.assertEqual(len(savedList), 1)
        self.assertEqual(savedList[0]["successCount"], 3)

    def testRankWorkingProxyListSortsAverageTimingAscending(self) -> None:
        service = ElasticIpPoolService(
            elasticIpHealthCheckProxy=FakeElasticIpHealthCheckProxy({}),
            keyValStoreProxy=FakeKeyValStoreProxy(),
            proxyScrapeProxy=FakeProxyScrapeProxy(),
        )

        resultList = service.rankWorkingProxyList(
            [
                {"proxy": "proxy-slow.example.net:8080", "averageTimingMs": 300},
                {"proxy": "proxy-fast.example.net:8080", "averageTimingMs": 100},
            ],
        )

        self.assertEqual(resultList[0]["proxy"], "proxy-fast.example.net:8080")

    def testSearchReturnsFastestProxy(self) -> None:
        service = ElasticIpPoolService(
            elasticIpHealthCheckProxy=FakeElasticIpHealthCheckProxy(
                {
                    "proxy-slow.example.net:8080": [
                        buildTestResult("proxy-slow.example.net:8080", True, 300),
                        buildTestResult("proxy-slow.example.net:8080", True, 300),
                        buildTestResult("proxy-slow.example.net:8080", True, 300),
                    ],
                    "proxy-fast.example.net:8080": [
                        buildTestResult("proxy-fast.example.net:8080", True, 100),
                        buildTestResult("proxy-fast.example.net:8080", True, 100),
                        buildTestResult("proxy-fast.example.net:8080", True, 100),
                    ],
                },
            ),
            keyValStoreProxy=FakeKeyValStoreProxy(),
            proxyScrapeProxy=FakeProxyScrapeProxy(
                "proxy-slow.example.net:8080\nproxy-fast.example.net:8080\n",
            ),
        )

        resultStr = service.search()

        self.assertEqual(resultStr, "proxy-fast.example.net:8080")

    def testSearchHandlesEmptyProxyScrapeResponse(self) -> None:
        keyValStoreProxy = FakeKeyValStoreProxy()
        service = ElasticIpPoolService(
            elasticIpHealthCheckProxy=FakeElasticIpHealthCheckProxy({}),
            keyValStoreProxy=keyValStoreProxy,
            proxyScrapeProxy=FakeProxyScrapeProxy(""),
        )

        resultStr = service.search()

        self.assertIsNone(resultStr)
        self.assertEqual(keyValStoreProxy.setValueCallCountInt, 0)

    def testSearchHandlesProxyScrapeApiFailure(self) -> None:
        service = ElasticIpPoolService(
            elasticIpHealthCheckProxy=FakeElasticIpHealthCheckProxy({}),
            keyValStoreProxy=FakeKeyValStoreProxy(),
            proxyScrapeProxy=FakeProxyScrapeProxy(error=ProxyScrapeProxyError("down")),
        )

        self.assertIsNone(service.search())

    def testGetHandlesCorruptedKeyValData(self) -> None:
        service = ElasticIpPoolService(
            elasticIpHealthCheckProxy=FakeElasticIpHealthCheckProxy(
                {
                    "proxy-new.example.net:8080": [
                        buildTestResult("proxy-new.example.net:8080", True, 100),
                        buildTestResult("proxy-new.example.net:8080", True, 100),
                        buildTestResult("proxy-new.example.net:8080", True, 100),
                    ],
                },
            ),
            keyValStoreProxy=FakeKeyValStoreProxy(
                {"key": "stored-key", "exists": True, "value": "{broken-json"},
            ),
            proxyScrapeProxy=FakeProxyScrapeProxy("proxy-new.example.net:8080\n"),
        )

        resultStr = service.get()

        self.assertEqual(resultStr, "proxy-new.example.net:8080")

    def testSearchRaisesWhenKeyValSaveFails(self) -> None:
        service = ElasticIpPoolService(
            elasticIpHealthCheckProxy=FakeElasticIpHealthCheckProxy(
                {
                    "proxy-new.example.net:8080": [
                        buildTestResult("proxy-new.example.net:8080", True, 100),
                        buildTestResult("proxy-new.example.net:8080", True, 100),
                        buildTestResult("proxy-new.example.net:8080", True, 100),
                    ],
                },
            ),
            keyValStoreProxy=FakeKeyValStoreProxy(storedBool=False),
            proxyScrapeProxy=FakeProxyScrapeProxy("proxy-new.example.net:8080\n"),
        )

        with self.assertRaises(RuntimeError):
            service.search()

    def testSearchHandlesTimeoutDuringProxyTesting(self) -> None:
        keyValStoreProxy = FakeKeyValStoreProxy()
        service = ElasticIpPoolService(
            elasticIpHealthCheckProxy=FakeElasticIpHealthCheckProxy(
                {
                    "proxy-new.example.net:8080": [
                        buildTestResult(
                            "proxy-new.example.net:8080",
                            False,
                            None,
                            "TimeoutError",
                        ),
                    ],
                },
            ),
            keyValStoreProxy=keyValStoreProxy,
            proxyScrapeProxy=FakeProxyScrapeProxy("proxy-new.example.net:8080\n"),
        )

        resultStr = service.search()

        self.assertIsNone(resultStr)
        self.assertEqual(keyValStoreProxy.setValueCallCountInt, 0)

    def testUpdateStoresCustomDummyProxyValueAtHashedKey(self) -> None:
        expectedKeyStr = hashStringValue(KEY_VAL_DUMMY_PROXY_KEY_STR)
        keyValStoreProxy = FakeKeyValStoreProxy()
        service = ElasticIpPoolService(
            keyValStoreProxy=keyValStoreProxy,
            dummyProxyValueStr="http://proxy-one.example.net:8080",
        )

        resultStr = service.update()

        self.assertEqual(resultStr, "http://proxy-one.example.net:8080")
        self.assertEqual(keyValStoreProxy.setKeyStr, expectedKeyStr)
        self.assertEqual(keyValStoreProxy.setValueStr, "http://proxy-one.example.net:8080")

    def testUpdateUsesCustomKeyValStoreProxySourceString(self) -> None:
        expectedKeyStr = hashStringValue("custom-key-source")
        keyValStoreProxy = FakeKeyValStoreProxy()
        service = ElasticIpPoolService(
            keyValStoreProxy=keyValStoreProxy,
            keyValStoreProxyStr="custom-key-source",
            dummyProxyValueStr=KEY_VAL_DUMMY_PROXY_VALUE_STR,
        )

        resultStr = service.update()

        self.assertEqual(resultStr, KEY_VAL_DUMMY_PROXY_VALUE_STR)
        self.assertEqual(keyValStoreProxy.setKeyStr, expectedKeyStr)
        self.assertEqual(keyValStoreProxy.setValueStr, KEY_VAL_DUMMY_PROXY_VALUE_STR)

    @unittest.skip("Placeholder until Elastic IP pool selection rules are implemented.")
    def testGetAvailableResourceReturnsOnlyUsableResource(self) -> None:
        service = ElasticIpPoolService(
            ElasticIpPoolRepo(),
            ElasticIpHealthCheckProxy(),
            KeyValStoreProxy(),
        )

        resourceDict = service.getAvailableResource()

        self.assertIsNotNone(resourceDict)


if __name__ == "__main__":
    unittest.main()
