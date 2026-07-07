import json
import unittest

from n_elastic_ip_pool.constant.elastic_ip_pool_constant import (
    KEY_VAL_DUMMY_PROXY_KEY_STR,
    KEY_VAL_MAX_VALUE_LENGTH_INT,
    MAX_PROXY_USAGE_COUNT_INT,
    PROXY_SOURCE_GEONODE_FREE_DISCOVERED_PROXY_STR,
    PROXY_SOURCE_PROXYSCRAPE_DISCOVERED_PROXY_STR,
    PROXY_SELECTION_MODE_RANDOM_STR,
)
from n_elastic_ip_pool.helper.string_hash_helper import hashStringValue
from n_elastic_ip_pool.proxy.elastic_ip_health_check_proxy import ElasticIpHealthCheckProxy
from n_elastic_ip_pool.proxy.geonode_free_proxy_list_proxy import (
    GeonodeFreeProxyListProxyError,
)
from n_elastic_ip_pool.proxy.key_val_store_proxy import KeyValStoreProxy
from n_elastic_ip_pool.proxy.proxy_scrape_proxy import ProxyScrapeProxyError
from n_elastic_ip_pool.repo.elastic_ip_pool_repo import ElasticIpPoolRepo
from n_elastic_ip_pool.service.elastic_ip_pool_service import ElasticIpPoolService


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


class FakeGeonodeFreeProxyListProxy:
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
            "url": "https://geonode.example.test",
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


class FakeProxyUsageHistoryRepo:
    def __init__(
        self,
        usageCountByProxyDict: dict[str, int] | None = None,
        disabledProxySet: set[str] | None = None,
    ) -> None:
        self.usageCountByProxyDict = dict(usageCountByProxyDict or {})
        self.disabledProxySet = set(disabledProxySet or set())
        self.recordProxyUsageCallList: list[tuple[str, dict | None]] = []
        self.markProxyDisabledCallList: list[str] = []

    def getProxyUsageCount(self, proxyStr: str) -> int:
        return int(self.usageCountByProxyDict.get(proxyStr, 0))

    def isProxyDisabled(self, proxyStr: str) -> bool:
        return proxyStr in self.disabledProxySet

    def recordProxyUsage(
        self,
        proxyStr: str,
        usageRecordDict: dict | None = None,
    ) -> dict:
        self.recordProxyUsageCallList.append((proxyStr, usageRecordDict))
        self.usageCountByProxyDict[proxyStr] = self.getProxyUsageCount(proxyStr) + 1
        return {
            "proxy": proxyStr,
            "usage_count": self.usageCountByProxyDict[proxyStr],
            "disabled": proxyStr in self.disabledProxySet,
        }

    def markProxyDisabled(self, proxyStr: str) -> dict:
        self.markProxyDisabledCallList.append(proxyStr)
        self.disabledProxySet.add(proxyStr)
        return {
            "proxy": proxyStr,
            "usage_count": self.getProxyUsageCount(proxyStr),
            "disabled": True,
        }


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
            keyValStoreProxyStr="custom-key-source",
            saveWorkingProxyBool=True,
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
        geonodeFreeProxyListProxy = FakeGeonodeFreeProxyListProxy(
            "geonode-new.example.net:8080\n",
        )
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
            geonodeFreeProxyListProxy=geonodeFreeProxyListProxy,
        )

        service.search()

        self.assertEqual(proxyScrapeProxy.fetchCallCountInt, 1)
        self.assertEqual(geonodeFreeProxyListProxy.fetchCallCountInt, 0)

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
            keyValStoreProxyStr="custom-key-source",
            saveWorkingProxyBool=True,
        )

        resultStr = service.search()
        savedList = json.loads(keyValStoreProxy.setValueStr)

        self.assertEqual(resultStr, "proxy-two.example.net:8080")
        self.assertEqual(len(savedList), 1)
        self.assertEqual(savedList[0], "proxy-two.example.net:8080")

    def testSearchDoesNotSaveWorkingProxyListByDefault(self) -> None:
        keyValStoreProxy = FakeKeyValStoreProxy()
        service = ElasticIpPoolService(
            elasticIpHealthCheckProxy=FakeElasticIpHealthCheckProxy(
                {
                    "proxy-new.example.net:8080": [
                        buildTestResult("proxy-new.example.net:8080", True, 100),
                    ],
                },
            ),
            keyValStoreProxy=keyValStoreProxy,
            proxyScrapeProxy=FakeProxyScrapeProxy("proxy-new.example.net:8080\n"),
            proxyValidationSuccessCountInt=1,
        )

        resultStr = service.search()

        self.assertEqual(resultStr, "proxy-new.example.net:8080")
        self.assertEqual(keyValStoreProxy.setValueCallCountInt, 0)
        self.assertEqual(keyValStoreProxy.setValueStr, "")

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

    def testSearchRejectsProxySlowerThanMaxTiming(self) -> None:
        keyValStoreProxy = FakeKeyValStoreProxy()
        service = ElasticIpPoolService(
            elasticIpHealthCheckProxy=FakeElasticIpHealthCheckProxy(
                {
                    "proxy-slow.example.net:8080": [
                        buildTestResult("proxy-slow.example.net:8080", True, 5001),
                    ],
                },
            ),
            keyValStoreProxy=keyValStoreProxy,
            proxyScrapeProxy=FakeProxyScrapeProxy("proxy-slow.example.net:8080\n"),
            geonodeFreeProxyListProxy=FakeGeonodeFreeProxyListProxy(),
        )

        resultStr = service.search()

        self.assertIsNone(resultStr)
        self.assertEqual(keyValStoreProxy.setValueCallCountInt, 0)

    def testSearchHandlesEmptyProxyScrapeResponse(self) -> None:
        keyValStoreProxy = FakeKeyValStoreProxy()
        service = ElasticIpPoolService(
            elasticIpHealthCheckProxy=FakeElasticIpHealthCheckProxy({}),
            keyValStoreProxy=keyValStoreProxy,
            proxyScrapeProxy=FakeProxyScrapeProxy(""),
            geonodeFreeProxyListProxy=FakeGeonodeFreeProxyListProxy(),
        )

        resultStr = service.search()

        self.assertIsNone(resultStr)
        self.assertEqual(keyValStoreProxy.setValueCallCountInt, 0)
        self.assertEqual(keyValStoreProxy.setValueStr, "")

    def testSearchHandlesProxyScrapeApiFailure(self) -> None:
        keyValStoreProxy = FakeKeyValStoreProxy()
        service = ElasticIpPoolService(
            elasticIpHealthCheckProxy=FakeElasticIpHealthCheckProxy({}),
            keyValStoreProxy=keyValStoreProxy,
            proxyScrapeProxy=FakeProxyScrapeProxy(error=ProxyScrapeProxyError("down")),
            geonodeFreeProxyListProxy=FakeGeonodeFreeProxyListProxy(),
        )

        self.assertIsNone(service.search())
        self.assertEqual(keyValStoreProxy.setValueCallCountInt, 0)
        self.assertEqual(keyValStoreProxy.setValueStr, "")

    def testSearchFallsBackToGeonodeWhenProxyScrapeFetchFails(self) -> None:
        geonodeFreeProxyListProxy = FakeGeonodeFreeProxyListProxy(
            "geonode-one.example.net:8080\n",
        )
        service = ElasticIpPoolService(
            elasticIpHealthCheckProxy=FakeElasticIpHealthCheckProxy(
                {
                    "geonode-one.example.net:8080": [
                        buildTestResult("geonode-one.example.net:8080", True, 90),
                    ],
                },
            ),
            keyValStoreProxy=FakeKeyValStoreProxy(),
            proxyScrapeProxy=FakeProxyScrapeProxy(error=ProxyScrapeProxyError("down")),
            geonodeFreeProxyListProxy=geonodeFreeProxyListProxy,
            proxyValidationSuccessCountInt=1,
        )

        resultStr = service.search()

        self.assertEqual(resultStr, "geonode-one.example.net:8080")
        self.assertEqual(geonodeFreeProxyListProxy.fetchCallCountInt, 1)

    def testSearchFallsBackToGeonodeWhenProxyScrapeCandidateDataIsMalformed(
        self,
    ) -> None:
        geonodeFreeProxyListProxy = FakeGeonodeFreeProxyListProxy(
            "geonode-one.example.net:8080\n",
        )
        service = ElasticIpPoolService(
            elasticIpHealthCheckProxy=FakeElasticIpHealthCheckProxy(
                {
                    "geonode-one.example.net:8080": [
                        buildTestResult("geonode-one.example.net:8080", True, 90),
                    ],
                },
            ),
            keyValStoreProxy=FakeKeyValStoreProxy(),
            proxyScrapeProxy=FakeProxyScrapeProxy("not-a-proxy\nalso-bad\n"),
            geonodeFreeProxyListProxy=geonodeFreeProxyListProxy,
            proxyValidationSuccessCountInt=1,
        )

        resultStr = service.search()

        self.assertEqual(resultStr, "geonode-one.example.net:8080")
        self.assertEqual(geonodeFreeProxyListProxy.fetchCallCountInt, 1)

    def testSearchFallsBackToGeonodeWhenProxyScrapeCandidatesFailValidation(
        self,
    ) -> None:
        healthCheckProxy = FakeElasticIpHealthCheckProxy(
            {
                "proxyscrape-bad.example.net:8080": [
                    buildTestResult(
                        "proxyscrape-bad.example.net:8080",
                        False,
                        None,
                        "timeout",
                    ),
                ],
                "geonode-one.example.net:8080": [
                    buildTestResult("geonode-one.example.net:8080", True, 90),
                ],
            },
        )
        geonodeFreeProxyListProxy = FakeGeonodeFreeProxyListProxy(
            "geonode-one.example.net:8080\n",
        )
        service = ElasticIpPoolService(
            elasticIpHealthCheckProxy=healthCheckProxy,
            keyValStoreProxy=FakeKeyValStoreProxy(),
            proxyScrapeProxy=FakeProxyScrapeProxy("proxyscrape-bad.example.net:8080\n"),
            geonodeFreeProxyListProxy=geonodeFreeProxyListProxy,
            proxyValidationSuccessCountInt=1,
        )

        resultStr = service.search()

        self.assertEqual(resultStr, "geonode-one.example.net:8080")
        self.assertEqual(geonodeFreeProxyListProxy.fetchCallCountInt, 1)
        self.assertEqual(
            healthCheckProxy.testCallList,
            ["proxyscrape-bad.example.net:8080", "geonode-one.example.net:8080"],
        )

    def testSearchReturnsFastestValidatedGeonodeProxyWhenFallbackSucceeds(
        self,
    ) -> None:
        service = ElasticIpPoolService(
            elasticIpHealthCheckProxy=FakeElasticIpHealthCheckProxy(
                {
                    "geonode-slow.example.net:8080": [
                        buildTestResult("geonode-slow.example.net:8080", True, 300),
                    ],
                    "geonode-fast.example.net:8080": [
                        buildTestResult("geonode-fast.example.net:8080", True, 80),
                    ],
                },
            ),
            keyValStoreProxy=FakeKeyValStoreProxy(),
            proxyScrapeProxy=FakeProxyScrapeProxy(""),
            geonodeFreeProxyListProxy=FakeGeonodeFreeProxyListProxy(
                "geonode-slow.example.net:8080\n"
                "geonode-fast.example.net:8080\n",
            ),
            proxyValidationSuccessCountInt=1,
        )

        resultStr = service.search()

        self.assertEqual(resultStr, "geonode-fast.example.net:8080")
        self.assertEqual(
            service.rankedProxyList,
            ["geonode-fast.example.net:8080", "geonode-slow.example.net:8080"],
        )

    def testSearchReturnsNoneWhenBothDiscoveryProvidersFail(self) -> None:
        keyValStoreProxy = FakeKeyValStoreProxy()
        service = ElasticIpPoolService(
            elasticIpHealthCheckProxy=FakeElasticIpHealthCheckProxy({}),
            keyValStoreProxy=keyValStoreProxy,
            proxyScrapeProxy=FakeProxyScrapeProxy(error=ProxyScrapeProxyError("down")),
            geonodeFreeProxyListProxy=FakeGeonodeFreeProxyListProxy(
                error=GeonodeFreeProxyListProxyError("down"),
            ),
            proxyValidationSuccessCountInt=1,
        )

        resultStr = service.search()

        self.assertIsNone(resultStr)
        self.assertEqual(keyValStoreProxy.setValueCallCountInt, 0)

    def testSearchSavesWorkingGeonodeProxyWhenSaveConfigurationAllowsIt(
        self,
    ) -> None:
        keyValStoreProxy = FakeKeyValStoreProxy()
        service = ElasticIpPoolService(
            elasticIpHealthCheckProxy=FakeElasticIpHealthCheckProxy(
                {
                    "geonode-one.example.net:8080": [
                        buildTestResult("geonode-one.example.net:8080", True, 90),
                    ],
                },
            ),
            keyValStoreProxy=keyValStoreProxy,
            proxyScrapeProxy=FakeProxyScrapeProxy(""),
            geonodeFreeProxyListProxy=FakeGeonodeFreeProxyListProxy(
                "geonode-one.example.net:8080\n",
            ),
            keyValStoreProxyStr="custom-key-source",
            saveWorkingProxyBool=True,
            proxyValidationSuccessCountInt=1,
        )

        resultStr = service.search()
        savedList = json.loads(keyValStoreProxy.setValueStr)

        self.assertEqual(resultStr, "geonode-one.example.net:8080")
        self.assertEqual(savedList, ["geonode-one.example.net:8080"])

    def testSearchDoesNotSaveWorkingGeonodeProxyWhenSaveDisabled(self) -> None:
        keyValStoreProxy = FakeKeyValStoreProxy()
        service = ElasticIpPoolService(
            elasticIpHealthCheckProxy=FakeElasticIpHealthCheckProxy(
                {
                    "geonode-one.example.net:8080": [
                        buildTestResult("geonode-one.example.net:8080", True, 90),
                    ],
                },
            ),
            keyValStoreProxy=keyValStoreProxy,
            proxyScrapeProxy=FakeProxyScrapeProxy(""),
            geonodeFreeProxyListProxy=FakeGeonodeFreeProxyListProxy(
                "geonode-one.example.net:8080\n",
            ),
            saveWorkingProxyBool=False,
            proxyValidationSuccessCountInt=1,
        )

        resultStr = service.search()

        self.assertEqual(resultStr, "geonode-one.example.net:8080")
        self.assertEqual(keyValStoreProxy.setValueCallCountInt, 0)
        self.assertEqual(keyValStoreProxy.setValueStr, "")

    def testSearchRecordsSuccessfulGeonodeFallbackUsageThroughRepo(self) -> None:
        usageHistoryRepo = FakeProxyUsageHistoryRepo()
        service = ElasticIpPoolService(
            elasticIpHealthCheckProxy=FakeElasticIpHealthCheckProxy(
                {
                    "geonode-one.example.net:8080": [
                        buildTestResult("geonode-one.example.net:8080", True, 90),
                    ],
                },
            ),
            keyValStoreProxy=FakeKeyValStoreProxy(),
            proxyScrapeProxy=FakeProxyScrapeProxy(""),
            geonodeFreeProxyListProxy=FakeGeonodeFreeProxyListProxy(
                "geonode-one.example.net:8080\n",
            ),
            proxyUsageHistoryRepo=usageHistoryRepo,
            proxyValidationSuccessCountInt=1,
        )

        resultStr = service.search()

        self.assertEqual(resultStr, "geonode-one.example.net:8080")
        self.assertEqual(
            usageHistoryRepo.recordProxyUsageCallList[0][0],
            "geonode-one.example.net:8080",
        )
        self.assertEqual(
            usageHistoryRepo.recordProxyUsageCallList[0][1]["source"],
            PROXY_SOURCE_GEONODE_FREE_DISCOVERED_PROXY_STR,
        )

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

    def testSearchReturnsWorkingProxyWhenKeyValSaveFails(self) -> None:
        keyValStoreProxy = FakeKeyValStoreProxy(storedBool=False)
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
            keyValStoreProxy=keyValStoreProxy,
            proxyScrapeProxy=FakeProxyScrapeProxy("proxy-new.example.net:8080\n"),
            keyValStoreProxyStr="custom-key-source",
            saveWorkingProxyBool=True,
        )

        resultStr = service.search()

        self.assertEqual(resultStr, "proxy-new.example.net:8080")
        self.assertEqual(keyValStoreProxy.setValueCallCountInt, 1)

    def testBuildSavedProxyValueStrStopsBeforeKeyValValueLimit(self) -> None:
        service = ElasticIpPoolService(
            elasticIpHealthCheckProxy=FakeElasticIpHealthCheckProxy({}),
            keyValStoreProxy=FakeKeyValStoreProxy(),
            proxyScrapeProxy=FakeProxyScrapeProxy(),
        )

        valueStr = service.buildSavedProxyValueStr(
            [
                {"proxy": "192.0.2.10:1081"},
                {"proxy": "198.51.100.20:9090"},
                {"proxy": "203.0.113.30:1080"},
                {"proxy": "192.0.2.40:443"},
                {"proxy": "198.51.100.50:443"},
                {"proxy": "203.0.113.60:82"},
            ],
        )
        savedProxyList = json.loads(valueStr)

        self.assertLessEqual(len(valueStr), KEY_VAL_MAX_VALUE_LENGTH_INT)
        self.assertEqual(
            savedProxyList,
            [
                "192.0.2.10:1081",
                "198.51.100.20:9090",
                "203.0.113.30:1080",
                "192.0.2.40:443",
                "198.51.100.50:443",
            ],
        )

    def testSearchLimitsRankedAndSavedProxyCount(self) -> None:
        keyValStoreProxy = FakeKeyValStoreProxy()
        service = ElasticIpPoolService(
            elasticIpHealthCheckProxy=FakeElasticIpHealthCheckProxy(
                {
                    "proxy-one.example.net:8080": [
                        buildTestResult("proxy-one.example.net:8080", True, 300),
                    ],
                    "proxy-two.example.net:8080": [
                        buildTestResult("proxy-two.example.net:8080", True, 100),
                    ],
                    "proxy-three.example.net:8080": [
                        buildTestResult("proxy-three.example.net:8080", True, 200),
                    ],
                },
            ),
            keyValStoreProxy=keyValStoreProxy,
            proxyScrapeProxy=FakeProxyScrapeProxy(
                "proxy-one.example.net:8080\n"
                "proxy-two.example.net:8080\n"
                "proxy-three.example.net:8080\n",
            ),
            proxyValidationSuccessCountInt=1,
            proxyResultCountInt=2,
            keyValStoreProxyStr="custom-key-source",
            saveWorkingProxyBool=True,
        )

        resultStr = service.search()
        savedProxyList = json.loads(keyValStoreProxy.setValueStr)

        self.assertEqual(resultStr, "proxy-two.example.net:8080")
        self.assertEqual(
            service.rankedProxyList,
            ["proxy-two.example.net:8080", "proxy-three.example.net:8080"],
        )
        self.assertEqual(
            savedProxyList,
            ["proxy-two.example.net:8080", "proxy-three.example.net:8080"],
        )

    def testGetCanSkipSavedProxyCache(self) -> None:
        keyValStoreProxy = FakeKeyValStoreProxy(
            {
                "key": "stored-key",
                "exists": True,
                "value": '["saved-fast.example.net:8080"]',
            },
        )
        proxyScrapeProxy = FakeProxyScrapeProxy("proxy-new.example.net:8080\n")
        service = ElasticIpPoolService(
            elasticIpHealthCheckProxy=FakeElasticIpHealthCheckProxy(
                {
                    "proxy-new.example.net:8080": [
                        buildTestResult("proxy-new.example.net:8080", True, 90),
                    ],
                },
            ),
            keyValStoreProxy=keyValStoreProxy,
            proxyScrapeProxy=proxyScrapeProxy,
            proxyValidationSuccessCountInt=1,
            useSavedProxyBool=False,
        )

        resultStr = service.get()

        self.assertEqual(resultStr, "proxy-new.example.net:8080")
        self.assertEqual(keyValStoreProxy.getKeyStr, "")
        self.assertEqual(proxyScrapeProxy.fetchCallCountInt, 1)

    def testSearchCanSkipSavingWorkingProxyList(self) -> None:
        keyValStoreProxy = FakeKeyValStoreProxy()
        service = ElasticIpPoolService(
            elasticIpHealthCheckProxy=FakeElasticIpHealthCheckProxy(
                {
                    "proxy-new.example.net:8080": [
                        buildTestResult("proxy-new.example.net:8080", True, 90),
                    ],
                },
            ),
            keyValStoreProxy=keyValStoreProxy,
            proxyScrapeProxy=FakeProxyScrapeProxy("proxy-new.example.net:8080\n"),
            proxyValidationSuccessCountInt=1,
            saveWorkingProxyBool=False,
        )

        resultStr = service.search()

        self.assertEqual(resultStr, "proxy-new.example.net:8080")
        self.assertEqual(keyValStoreProxy.setValueCallCountInt, 0)
        self.assertEqual(keyValStoreProxy.setValueStr, "")

    def testCandidateShuffleAndLimitAreDeterministicWithSeed(self) -> None:
        healthCheckProxy = FakeElasticIpHealthCheckProxy(
            {
                "proxy-one.example.net:8080": [
                    buildTestResult("proxy-one.example.net:8080", True, 100),
                ],
                "proxy-two.example.net:8080": [
                    buildTestResult("proxy-two.example.net:8080", True, 100),
                ],
                "proxy-three.example.net:8080": [
                    buildTestResult("proxy-three.example.net:8080", True, 100),
                ],
            },
        )
        service = ElasticIpPoolService(
            elasticIpHealthCheckProxy=healthCheckProxy,
            keyValStoreProxy=FakeKeyValStoreProxy(),
            proxyScrapeProxy=FakeProxyScrapeProxy(
                "proxy-one.example.net:8080\n"
                "proxy-two.example.net:8080\n"
                "proxy-three.example.net:8080\n",
            ),
            proxyValidationSuccessCountInt=1,
            proxyShuffleCandidateBool=True,
            proxyRandomSeedInt=7,
            proxyCandidateLimitInt=2,
        )

        service.search()

        self.assertEqual(
            healthCheckProxy.testCallList,
            ["proxy-three.example.net:8080", "proxy-one.example.net:8080"],
        )

    def testRandomSelectionModeUsesSeededWorkingProxyOrder(self) -> None:
        service = ElasticIpPoolService(
            elasticIpHealthCheckProxy=FakeElasticIpHealthCheckProxy({}),
            keyValStoreProxy=FakeKeyValStoreProxy(),
            proxyScrapeProxy=FakeProxyScrapeProxy(),
            proxySelectionModeStr=PROXY_SELECTION_MODE_RANDOM_STR,
            proxyRandomSeedInt=42,
        )

        resultList = service.rankWorkingProxyList(
            [
                {"proxy": "proxy-one.example.net:8080", "averageTimingMs": 100},
                {"proxy": "proxy-two.example.net:8080", "averageTimingMs": 200},
                {"proxy": "proxy-three.example.net:8080", "averageTimingMs": 300},
            ],
        )

        self.assertEqual(
            [proxyDict["proxy"] for proxyDict in resultList],
            [
                "proxy-two.example.net:8080",
                "proxy-one.example.net:8080",
                "proxy-three.example.net:8080",
            ],
        )

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
            geonodeFreeProxyListProxy=FakeGeonodeFreeProxyListProxy(),
        )

        resultStr = service.search()

        self.assertIsNone(resultStr)
        self.assertEqual(keyValStoreProxy.setValueCallCountInt, 0)
        self.assertEqual(keyValStoreProxy.setValueStr, "")

    def testUpdateRequiresExplicitProxyListValue(self) -> None:
        keyValStoreProxy = FakeKeyValStoreProxy()
        service = ElasticIpPoolService(keyValStoreProxy=keyValStoreProxy)

        with self.assertRaises(ValueError):
            service.update(None)

        self.assertEqual(keyValStoreProxy.setValueCallCountInt, 0)

    def testUpdateRequiresCustomSaveTarget(self) -> None:
        service = ElasticIpPoolService()

        with self.assertRaises(ValueError):
            service.update('["proxy-one.example.net:8080"]')

    def testUpdateUsesCustomKeyValStoreProxySourceString(self) -> None:
        expectedKeyStr = hashStringValue("custom-key-source")
        keyValStoreProxy = FakeKeyValStoreProxy()
        service = ElasticIpPoolService(
            keyValStoreProxy=keyValStoreProxy,
            keyValStoreProxyStr="custom-key-source",
        )

        resultStr = service.update('["proxy-one.example.net:8080"]')

        self.assertEqual(resultStr, '["proxy-one.example.net:8080"]')
        self.assertEqual(keyValStoreProxy.setKeyStr, expectedKeyStr)
        self.assertEqual(
            keyValStoreProxy.setValueStr,
            '["proxy-one.example.net:8080"]',
        )

    def testSearchRecordsSuccessfulProxyUsageThroughRepo(self) -> None:
        usageHistoryRepo = FakeProxyUsageHistoryRepo()
        service = ElasticIpPoolService(
            elasticIpHealthCheckProxy=FakeElasticIpHealthCheckProxy(
                {
                    "proxy-one.example.net:8080": [
                        buildTestResult("proxy-one.example.net:8080", True, 90),
                    ],
                },
            ),
            keyValStoreProxy=FakeKeyValStoreProxy(),
            proxyScrapeProxy=FakeProxyScrapeProxy("proxy-one.example.net:8080\n"),
            proxyUsageHistoryRepo=usageHistoryRepo,
            proxyValidationSuccessCountInt=1,
        )

        resultStr = service.search()

        self.assertEqual(resultStr, "proxy-one.example.net:8080")
        self.assertEqual(
            usageHistoryRepo.recordProxyUsageCallList[0][0],
            "proxy-one.example.net:8080",
        )
        self.assertEqual(
            usageHistoryRepo.recordProxyUsageCallList[0][1]["source"],
            PROXY_SOURCE_PROXYSCRAPE_DISCOVERED_PROXY_STR,
        )

    def testSearchSkipsAndDisablesProxyAtHistoricUsageLimit(self) -> None:
        usageHistoryRepo = FakeProxyUsageHistoryRepo(
            usageCountByProxyDict={
                "proxy-one.example.net:8080": MAX_PROXY_USAGE_COUNT_INT,
            },
        )
        healthCheckProxy = FakeElasticIpHealthCheckProxy(
            {
                "proxy-two.example.net:8080": [
                    buildTestResult("proxy-two.example.net:8080", True, 100),
                ],
            },
        )
        service = ElasticIpPoolService(
            elasticIpHealthCheckProxy=healthCheckProxy,
            keyValStoreProxy=FakeKeyValStoreProxy(),
            proxyScrapeProxy=FakeProxyScrapeProxy(
                "proxy-one.example.net:8080\nproxy-two.example.net:8080\n",
            ),
            proxyUsageHistoryRepo=usageHistoryRepo,
            proxyValidationSuccessCountInt=1,
            geonodeFreeProxyListProxy=FakeGeonodeFreeProxyListProxy(),
        )

        resultStr = service.search()

        self.assertEqual(resultStr, "proxy-two.example.net:8080")
        self.assertEqual(healthCheckProxy.testCallList, ["proxy-two.example.net:8080"])
        self.assertIn(
            "proxy-one.example.net:8080",
            usageHistoryRepo.markProxyDisabledCallList,
        )

    def testSearchReturnsNoneWhenAllCandidatesFailedDisabledOrOverused(self) -> None:
        usageHistoryRepo = FakeProxyUsageHistoryRepo(
            usageCountByProxyDict={
                "proxy-two.example.net:8080": MAX_PROXY_USAGE_COUNT_INT,
            },
            disabledProxySet={"proxy-one.example.net:8080"},
        )
        healthCheckProxy = FakeElasticIpHealthCheckProxy(
            {
                "proxy-three.example.net:8080": [
                    buildTestResult(
                        "proxy-three.example.net:8080",
                        False,
                        None,
                        "timeout",
                    ),
                ],
            },
        )
        service = ElasticIpPoolService(
            elasticIpHealthCheckProxy=healthCheckProxy,
            keyValStoreProxy=FakeKeyValStoreProxy(),
            proxyScrapeProxy=FakeProxyScrapeProxy(
                "proxy-one.example.net:8080\n"
                "proxy-two.example.net:8080\n"
                "proxy-three.example.net:8080\n",
            ),
            proxyUsageHistoryRepo=usageHistoryRepo,
            proxyValidationSuccessCountInt=1,
            geonodeFreeProxyListProxy=FakeGeonodeFreeProxyListProxy(),
        )

        resultStr = service.search()

        self.assertIsNone(resultStr)
        self.assertEqual(healthCheckProxy.testCallList, ["proxy-three.example.net:8080"])
        self.assertEqual(usageHistoryRepo.recordProxyUsageCallList, [])

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
