import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.key_value_proxy_app import buildVerboseElasticIpPoolService
from n_elastic_ip_pool.constant.elastic_ip_pool_constant import (
    DEFAULT_KEY_VAL_PROXY_TRANSLATION_COUNT_KEY_STR,
)
from n_elastic_ip_pool.proxy.key_val_store_proxy import KeyValStoreProxyError
from n_elastic_ip_pool.proxy.key_val_store_proxy import KeyValStoreProxy
from n_elastic_ip_pool.service.elastic_ip_pool_service import ElasticIpPoolService
from n_elastic_ip_pool.service.verbose_elastic_ip_pool_service import VerboseElasticIpPoolService
from test.service.test_elastic_ip_pool_service import (
    FakeElasticIpHealthCheckProxy,
    FakeGeonodeFreeProxyListProxy,
    FakeProxyScrapeProxy,
    FakeProxyUsageHistoryRepo,
    buildTestResult,
)


class MemoryKeyValStoreProxy(KeyValStoreProxy):
    def __init__(self) -> None:
        super().__init__(baseUrlStr="https://keyval.example.test")
        self.valueByKeyDict: dict[str, str] = {}
        self.writeList: list[tuple[str, str]] = []
        self.readErrorBool = False
        self.writeErrorBool = False
        self.storedBool = True

    def getValue(self, keyStr: str) -> dict:
        if self.readErrorBool:
            raise KeyValStoreProxyError("offline")
        return {
            "exists": keyStr in self.valueByKeyDict,
            "value": self.valueByKeyDict.get(keyStr),
        }

    def setValue(self, keyStr: str, valueStr: str) -> dict:
        self.writeList.append((keyStr, valueStr))
        if self.writeErrorBool:
            raise KeyValStoreProxyError("offline")
        if self.storedBool:
            self.valueByKeyDict[keyStr] = valueStr
        return {"stored": self.storedBool, "value": valueStr}


class ProxyTranslationFeedbackServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        environmentPatch = patch.dict(os.environ, {}, clear=True)
        environmentPatch.start()
        self.addCleanup(environmentPatch.stop)
        networkPatch = patch(
            "urllib.request.OpenerDirector.open",
            side_effect=AssertionError("Tests must not make network requests"),
        )
        networkPatch.start()
        self.addCleanup(networkPatch.stop)
        self.proxyStr = "proxy-one.example.net:8080"
        self.replacementStr = "proxy-two.example.net:8080"
        self.store = MemoryKeyValStoreProxy()

    def buildService(self, serviceClass=ElasticIpPoolService, **optionDict):
        defaultDict = {
            "keyValStoreProxy": self.store,
            "proxyScrapeProxy": FakeProxyScrapeProxy(
                f"{self.proxyStr}\n{self.replacementStr}\n",
            ),
            "geonodeFreeProxyListProxy": FakeGeonodeFreeProxyListProxy(),
            "elasticIpHealthCheckProxy": FakeElasticIpHealthCheckProxy({
                self.proxyStr: [buildTestResult(self.proxyStr, True, 10)] * 10,
                self.replacementStr: [buildTestResult(self.replacementStr, True, 20)] * 10,
            }),
            "proxyUsageHistoryRepo": FakeProxyUsageHistoryRepo(),
            "proxyValidationSuccessCountInt": 1,
            "envFilePathStr": "missing.env",
        }
        defaultDict.update(optionDict)
        return serviceClass(**defaultDict)

    def testDefaultsAndNamespaceIsolation(self) -> None:
        service = self.buildService()
        self.assertEqual(service.proxyTranslationMaxUseCountInt, 50)
        self.assertEqual(service.proxyTranslationMinHealthCountInt, -5)
        self.assertEqual(service.keyValProxyTranslationCountKeyStr,
                         DEFAULT_KEY_VAL_PROXY_TRANSLATION_COUNT_KEY_STR)
        keyStr = service.getKeyValProxyTranslationCountKey(self.proxyStr)
        self.assertNotEqual(keyStr, service.getKeyValProxyKey())
        self.assertEqual(len(keyStr), 64)
        for otherService, proxyStr in (
            (service, self.replacementStr),
            (self.buildService(keyValStoreProxyStr="another-pool"), self.proxyStr),
            (self.buildService(keyValProxyTranslationCountKeyStr="another-counter"), self.proxyStr),
        ):
            self.assertNotEqual(keyStr, otherService.getKeyValProxyTranslationCountKey(proxyStr))

    def testEnvironmentAndExplicitConstructorPrecedence(self) -> None:
        with patch.dict(os.environ, {
            "KEY_VAL_PROXY_TRANSLATION_COUNT_KEY": "subtitle-worker-counter",
            "PROXY_TRANSLATION_MAX_USE_COUNT": "999",
            "PROXY_TRANSLATION_MIN_HEALTH_COUNT": "-9",
        }):
            for serviceClass in (ElasticIpPoolService, VerboseElasticIpPoolService):
                service = self.buildService(serviceClass)
                self.assertEqual(service.keyValProxyTranslationCountKeyStr, "subtitle-worker-counter")
                self.assertEqual(service.proxyTranslationMaxUseCountInt, 999)
                self.assertEqual(service.proxyTranslationMinHealthCountInt, -9)
                explicitService = self.buildService(
                    serviceClass,
                    keyValProxyTranslationCountKeyStr="explicit-counter",
                    proxyTranslationMaxUseCountInt=1,
                    proxyTranslationMinHealthCountInt=-1,
                )
                self.assertEqual(explicitService.keyValProxyTranslationCountKeyStr, "explicit-counter")
                self.assertEqual(explicitService.proxyTranslationMaxUseCountInt, 1)
                self.assertEqual(explicitService.proxyTranslationMinHealthCountInt, -1)

    def testInvalidEnvironmentLimitsFallBack(self) -> None:
        for upperStr, lowerStr in (("", ""), ("invalid", "1.5"), ("0", "0"), ("-1", "1")):
            with self.subTest(upperStr=upperStr, lowerStr=lowerStr), patch.dict(os.environ, {
                "PROXY_TRANSLATION_MAX_USE_COUNT": upperStr,
                "PROXY_TRANSLATION_MIN_HEALTH_COUNT": lowerStr,
                "KEY_VAL_PROXY_TRANSLATION_COUNT_KEY": "   ",
            }):
                service = self.buildService()
                self.assertEqual(service.proxyTranslationMaxUseCountInt, 50)
                self.assertEqual(service.proxyTranslationMinHealthCountInt, -5)
                self.assertEqual(service.keyValProxyTranslationCountKeyStr,
                                 DEFAULT_KEY_VAL_PROXY_TRANSLATION_COUNT_KEY_STR)

    def testAppBuilderUsesCustomEnvFileAndProcessOverrides(self) -> None:
        with tempfile.TemporaryDirectory() as directoryStr:
            envPath = Path(directoryStr) / "fixture.env"
            envPath.write_text(
                "KEY_VAL_PROXY_TRANSLATION_COUNT_KEY=file-counter\n"
                "PROXY_TRANSLATION_MAX_USE_COUNT=12 # upper limit\n"
                "PROXY_TRANSLATION_MIN_HEALTH_COUNT=-3\n",
                encoding="utf-8",
            )
            service = buildVerboseElasticIpPoolService(str(envPath))
            self.assertEqual(service.keyValProxyTranslationCountKeyStr, "file-counter")
            self.assertEqual(service.proxyTranslationMaxUseCountInt, 12)
            self.assertEqual(service.proxyTranslationMinHealthCountInt, -3)
            with patch.dict(os.environ, {"PROXY_TRANSLATION_MAX_USE_COUNT": "15"}):
                self.assertEqual(
                    buildVerboseElasticIpPoolService(str(envPath)).proxyTranslationMaxUseCountInt,
                    15,
                )

    def testSuccessAndProxyFailurePersistSignedNumbersOnly(self) -> None:
        service = self.buildService()
        keyStr = service.getKeyValProxyTranslationCountKey(self.proxyStr)
        self.assertEqual(service.getProxyTranslationCount(self.proxyStr), 0)
        self.assertEqual(service.recordSubtitleTranslationResult(self.proxyStr, True), self.proxyStr)
        self.assertEqual(self.store.valueByKeyDict[keyStr], "1")
        for expectedStr in ("0", "-1"):
            self.assertEqual(service.recordSubtitleTranslationResult(self.proxyStr, False, True), self.proxyStr)
            self.assertEqual(self.store.valueByKeyDict[keyStr], expectedStr)
        self.assertEqual(self.buildService().getProxyTranslationCount(self.proxyStr), -1)
        self.assertEqual(service.proxyScrapeProxy.fetchCallCountInt, 0)

    def testUnrelatedFailureAndHealthChecksDoNotChangeTranslationCount(self) -> None:
        service = self.buildService()
        self.assertEqual(service.recordSubtitleTranslationResult(self.proxyStr, False), self.proxyStr)
        self.assertEqual(self.store.writeList, [])
        self.assertEqual(service.search(), self.proxyStr)
        self.assertEqual(service.check(), self.proxyStr)
        keyStr = service.getKeyValProxyTranslationCountKey(self.proxyStr)
        self.assertEqual(self.store.valueByKeyDict[keyStr], "0")
        self.assertEqual(service.getProxyTranslationCount(self.proxyStr), 0)

    def testBothExactThresholdsTriggerFreshDiscoveryAndIsolateReplacement(self) -> None:
        for startInt, successBool, expectedInt in ((49, True, 50), (-4, False, -5)):
            with self.subTest(startInt=startInt):
                self.store = MemoryKeyValStoreProxy()
                service = self.buildService()
                keyStr = service.getKeyValProxyTranslationCountKey(self.proxyStr)
                self.store.valueByKeyDict[keyStr] = str(startInt)
                self.store.valueByKeyDict[service.getKeyValProxyKey()] = json.dumps([self.proxyStr])
                resultStr = service.recordSubtitleTranslationResult(self.proxyStr, successBool, not successBool)
                self.assertEqual(resultStr, self.replacementStr)
                self.assertEqual(self.store.valueByKeyDict[keyStr], str(expectedInt))
                self.assertEqual(service.proxyScrapeProxy.fetchCallCountInt, 1)
                self.assertNotIn(self.proxyStr, service.elasticIpHealthCheckProxy.testCallList)
                self.assertEqual(service.rankedProxyList, [self.replacementStr])
                self.assertEqual(service.getProxyTranslationCount(self.replacementStr), 0)

    def testRestartSkipsPersistedThresholdAndOvershootInCacheAndDiscovery(self) -> None:
        for countInt in (50, 999, -5, -999):
            with self.subTest(countInt=countInt):
                service = self.buildService()
                self.store.valueByKeyDict[service.getKeyValProxyTranslationCountKey(self.proxyStr)] = str(countInt)
                self.store.valueByKeyDict[service.getKeyValProxyKey()] = json.dumps([self.proxyStr])
                self.assertEqual(service.get(), self.replacementStr)
                self.assertNotIn(self.proxyStr, service.elasticIpHealthCheckProxy.testCallList)
                self.assertEqual(service.proxyScrapeProxy.fetchCallCountInt, 1)

    def testNoReplacementReturnsNoneAndClearsVerboseResult(self) -> None:
        service = self.buildService(
            VerboseElasticIpPoolService,
            loggerLevelStr="CRITICAL",
            proxyScrapeProxy=FakeProxyScrapeProxy(self.proxyStr),
            proxyTranslationMaxUseCountInt=1,
        )
        service.finalValueStr = self.proxyStr
        self.assertIsNone(service.recordSubtitleTranslationResult(self.proxyStr, True))
        self.assertIsNone(service.finalValueStr)
        self.assertEqual(service.rankedProxyList, [])

    def testVerboseFeedbackUpdatesSelectedReplacement(self) -> None:
        service = self.buildService(
            VerboseElasticIpPoolService, loggerLevelStr="CRITICAL",
            proxyTranslationMaxUseCountInt=1,
        )
        self.assertEqual(service.recordSubtitleTranslationResult(self.proxyStr, True), self.replacementStr)
        self.assertEqual(service.finalValueStr, self.replacementStr)

    def testStorageFailuresRetainLocalProgressAndRetryWrite(self) -> None:
        for failureStr in ("read", "write", "not-stored"):
            with self.subTest(failureStr=failureStr):
                self.store = MemoryKeyValStoreProxy()
                service = self.buildService(proxyTranslationMaxUseCountInt=2)
                self.store.readErrorBool = failureStr == "read"
                self.store.writeErrorBool = failureStr in {"read", "write"}
                self.store.storedBool = failureStr != "not-stored"
                self.assertEqual(service.recordSubtitleTranslationResult(self.proxyStr, True), self.proxyStr)
                self.assertEqual(service.getProxyTranslationCount(self.proxyStr), 1)
                self.store.readErrorBool = False
                self.store.writeErrorBool = False
                self.store.storedBool = True
                self.assertEqual(service.recordSubtitleTranslationResult(self.proxyStr, True), self.replacementStr)
                keyStr = service.getKeyValProxyTranslationCountKey(self.proxyStr)
                self.assertEqual(self.store.valueByKeyDict[keyStr], "2")

    def testPersistentStorageOutageStillEnforcesLowerLimit(self) -> None:
        service = self.buildService()
        self.store.readErrorBool = True
        self.store.writeErrorBool = True
        for _ in range(4):
            self.assertEqual(service.recordSubtitleTranslationResult(self.proxyStr, False, True), self.proxyStr)
        self.assertEqual(service.recordSubtitleTranslationResult(self.proxyStr, False, True), self.replacementStr)
        self.assertEqual(service.getProxyTranslationCount(self.proxyStr), -5)

    def testMalformedStoredCountAndReadFailureRetainKnownCount(self) -> None:
        service = self.buildService()
        keyStr = service.getKeyValProxyTranslationCountKey(self.proxyStr)
        service.recordSubtitleTranslationResult(self.proxyStr, True)
        for valueStr in ("not-a-number", "[]", "1.5"):
            self.store.valueByKeyDict[keyStr] = valueStr
            self.assertEqual(service.getProxyTranslationCount(self.proxyStr), 1)
        self.store.readErrorBool = True
        self.assertEqual(service.getProxyTranslationCount(self.proxyStr), 1)

    def testDisabledPersistenceUsesOnlyLocalCounter(self) -> None:
        service = self.buildService(useSavedProxyBool=False, saveWorkingProxyBool=False)
        with patch.object(self.store, "getValue", side_effect=AssertionError("unexpected read")):
            self.assertEqual(service.recordSubtitleTranslationResult(self.proxyStr, True), self.proxyStr)
            self.assertEqual(service.getProxyTranslationCount(self.proxyStr), 1)
            self.assertEqual(service.search(), self.proxyStr)
        self.assertEqual(self.store.writeList, [])

    def testReadOnlyServiceDoesNotWriteFeedback(self) -> None:
        service = self.buildService(saveWorkingProxyBool=False)
        service.recordSubtitleTranslationResult(self.proxyStr, True)
        service.recordSubtitleTranslationResult(self.proxyStr, True)
        self.assertEqual(service.getProxyTranslationCount(self.proxyStr), 2)
        self.assertEqual(self.store.writeList, [])

    def testInvalidFeedbackDoesNotWrite(self) -> None:
        service = self.buildService()
        for proxyStr, successBool, failureBool in (("invalid", True, False), (self.proxyStr, True, True)):
            with self.assertRaises(ValueError):
                service.recordSubtitleTranslationResult(proxyStr, successBool, failureBool)
        self.assertEqual(self.store.writeList, [])

    def testLateSuccessCannotReviveFailedProxy(self) -> None:
        service = self.buildService()
        keyStr = service.getKeyValProxyTranslationCountKey(self.proxyStr)
        self.store.valueByKeyDict[keyStr] = "-5"
        self.assertEqual(service.recordSubtitleTranslationResult(self.proxyStr, True), self.replacementStr)
        self.assertEqual(self.store.valueByKeyDict[keyStr], "-5")

    def testFreshDiscoveryResetsEveryReturnedProxyCounter(self) -> None:
        service = self.buildService()
        for proxyStr, countStr in ((self.proxyStr, "20"), (self.replacementStr, "-3")):
            self.store.valueByKeyDict[service.getKeyValProxyTranslationCountKey(proxyStr)] = countStr
        self.assertEqual(service.search(), self.proxyStr)
        for proxyStr in service.rankedProxyList:
            self.assertEqual(service.getProxyTranslationCount(proxyStr), 0)
            self.assertEqual(self.store.valueByKeyDict[
                service.getKeyValProxyTranslationCountKey(proxyStr)
            ], "0")
        service.recordSubtitleTranslationResult(self.proxyStr, True)
        self.assertEqual(service.getProxyTranslationCount(self.proxyStr), 1)

    def testCachedProxyCheckDoesNotResetCounter(self) -> None:
        service = self.buildService()
        keyStr = service.getKeyValProxyTranslationCountKey(self.proxyStr)
        self.store.valueByKeyDict[keyStr] = "20"
        self.store.valueByKeyDict[service.getKeyValProxyKey()] = json.dumps([self.proxyStr])
        self.assertEqual(service.get(), self.proxyStr)
        self.assertEqual(self.store.valueByKeyDict[keyStr], "20")
        self.assertEqual(self.store.writeList, [])

    def testFallbackDiscoveryResetsCounter(self) -> None:
        service = self.buildService(
            proxyScrapeProxy=FakeProxyScrapeProxy(),
            geonodeFreeProxyListProxy=FakeGeonodeFreeProxyListProxy(self.proxyStr),
        )
        keyStr = service.getKeyValProxyTranslationCountKey(self.proxyStr)
        self.store.valueByKeyDict[keyStr] = "-2"
        self.assertEqual(service.search(), self.proxyStr)
        self.assertEqual(self.store.valueByKeyDict[keyStr], "0")

    def testFailedDiscoveryDoesNotResetCounter(self) -> None:
        service = self.buildService(elasticIpHealthCheckProxy=FakeElasticIpHealthCheckProxy({}))
        keyStr = service.getKeyValProxyTranslationCountKey(self.proxyStr)
        self.store.valueByKeyDict[keyStr] = "20"
        self.assertIsNone(service.search())
        self.assertEqual(self.store.valueByKeyDict[keyStr], "20")
        self.assertEqual(self.store.writeList, [])

    def testResetWriteFailureKeepsZeroLocallyUntilNextFeedback(self) -> None:
        service = self.buildService()
        keyStr = service.getKeyValProxyTranslationCountKey(self.proxyStr)
        self.store.valueByKeyDict[keyStr] = "20"
        self.store.writeErrorBool = True
        self.assertEqual(service.search(), self.proxyStr)
        self.assertEqual(service.getProxyTranslationCount(self.proxyStr), 0)
        self.assertEqual(self.store.valueByKeyDict[keyStr], "20")
        self.store.writeErrorBool = False
        service.recordSubtitleTranslationResult(self.proxyStr, True)
        self.assertEqual(self.store.valueByKeyDict[keyStr], "1")

    def testInfoLogsExactCounterKeyCountAndStorageStatusWithoutSecrets(self) -> None:
        service = self.buildService(
            VerboseElasticIpPoolService, loggerLevelStr="INFO",
            keyValProxyTranslationCountKeyStr="private-counter-namespace",
        )
        keyStr = service.getKeyValProxyTranslationCountKey(self.proxyStr)
        for storedBool in (True, False):
            self.store.storedBool = storedBool
            with patch("builtins.print") as printMock:
                service.resetProxyTranslationCount(self.proxyStr)
                service.recordSubtitleTranslationResult(self.proxyStr, True)
            textStr = "\n".join(
                " ".join(str(value) for value in call.args)
                for call in printMock.call_args_list
            )
            self.assertIn(f"[translation-count] key={keyStr} count=0", textStr)
            self.assertIn(f"[translation-count] key={keyStr} count=1", textStr)
            self.assertIn(f"stored={str(storedBool).lower()}", textStr)
            self.assertNotIn("private-counter-namespace", textStr)
            self.assertNotIn("https://", textStr)

    def testQuietLoggerSuppressesCounterInfo(self) -> None:
        service = self.buildService(VerboseElasticIpPoolService, loggerLevelStr="WARNING")
        with patch("builtins.print") as printMock:
            service.resetProxyTranslationCount(self.proxyStr)
        printMock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
