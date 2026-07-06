import unittest
from unittest.mock import patch

from core.constant.elastic_ip_pool_constant import (
    KEY_VAL_STORE_PROXY_ENV_NAME_STR,
    LOGGER_LEVEL_DEBUG_STR,
    PROXY_RELEASE_CHANNEL_CANARY_STR,
    PROXY_SELECTION_MODE_RANDOM_STR,
)
from testKeyValueProxy import (
    buildArgumentParser,
    buildRunOptionDict,
    buildVerboseElasticIpPoolService,
)


class KeyValueProxyRunnerTest(unittest.TestCase):
    def testBuildRunOptionDictUsesCanaryReleaseChannelDefaults(self) -> None:
        argumentNamespace = buildArgumentParser().parse_args(
            ["--release-channel", PROXY_RELEASE_CHANNEL_CANARY_STR],
        )

        runOptionDict = buildRunOptionDict(argumentNamespace)

        self.assertEqual(
            runOptionDict["releaseChannelStr"],
            PROXY_RELEASE_CHANNEL_CANARY_STR,
        )
        self.assertEqual(runOptionDict["proxyResultCountInt"], 5)
        self.assertEqual(
            runOptionDict["proxySelectionModeStr"],
            PROXY_SELECTION_MODE_RANDOM_STR,
        )
        self.assertEqual(runOptionDict["proxyCandidateLimitInt"], 500)
        self.assertTrue(runOptionDict["proxyShuffleCandidateBool"])
        self.assertEqual(runOptionDict["proxyValidationSuccessCountInt"], 2)
        self.assertEqual(runOptionDict["proxyMaxTimingMillisecondInt"], 3500)

    def testBuildServicePassesCustomRunOptions(self) -> None:
        argumentNamespace = buildArgumentParser().parse_args(
            [
                "--release-channel",
                "beta",
                "--key-source",
                "custom-key-source",
                "--log-level",
                LOGGER_LEVEL_DEBUG_STR,
                "--count",
                "2",
                "--selection-mode",
                PROXY_SELECTION_MODE_RANDOM_STR,
                "--candidate-limit",
                "9",
                "--shuffle-candidates",
                "--random-seed",
                "123",
                "--validation-count",
                "4",
                "--max-timing-ms",
                "1500",
                "--no-cache",
                "--no-save",
                "--provider-base-url",
                "https://proxy.example.test",
                "--provider-timeout-ms",
                "800",
                "--provider-timeout-second",
                "6",
                "--country",
                "US",
                "--proxy-type",
                "http",
                "--ssl",
                "yes",
                "--anonymity",
                "elite",
                "--target-url",
                "https://target.example.test/ip",
                "--keyval-base-url",
                "https://keyval.example.test",
            ],
        )

        service = buildVerboseElasticIpPoolService(argumentNamespace)

        self.assertEqual(service.releaseChannelStr, "beta")
        self.assertEqual(service.keyValStoreProxyStr, "custom-key-source")
        self.assertEqual(service.loggerLevelStr, LOGGER_LEVEL_DEBUG_STR)
        self.assertEqual(service.proxyResultCountInt, 2)
        self.assertEqual(service.proxySelectionModeStr, PROXY_SELECTION_MODE_RANDOM_STR)
        self.assertEqual(service.proxyCandidateLimitInt, 9)
        self.assertTrue(service.proxyShuffleCandidateBool)
        self.assertEqual(service.proxyRandomSeedInt, 123)
        self.assertEqual(service.proxyValidationSuccessCountInt, 4)
        self.assertEqual(service.proxyMaxTimingMillisecondInt, 1500)
        self.assertFalse(service.useSavedProxyBool)
        self.assertFalse(service.saveWorkingProxyBool)
        self.assertEqual(
            service.proxyScrapeProxy.baseUrlStr,
            "https://proxy.example.test",
        )
        self.assertEqual(service.proxyScrapeProxy.timeoutMillisecondInt, 800)
        self.assertEqual(service.proxyScrapeProxy.timeoutSecondInt, 6)
        self.assertEqual(service.proxyScrapeProxy.countryFilterStr, "US")
        self.assertEqual(service.proxyScrapeProxy.proxyTypeStr, "http")
        self.assertEqual(service.proxyScrapeProxy.sslFilterStr, "yes")
        self.assertEqual(service.proxyScrapeProxy.anonymityFilterStr, "elite")
        self.assertEqual(
            service.elasticIpHealthCheckProxy.targetUrlStr,
            "https://target.example.test/ip",
        )
        self.assertEqual(
            service.keyValStoreProxy.baseUrlStr,
            "https://keyval.example.test",
        )

    def testBuildServiceUsesEnvironmentKeySourceWhenCliValueIsMissing(self) -> None:
        argumentNamespace = buildArgumentParser().parse_args([])

        with patch.dict(
            "os.environ",
            {KEY_VAL_STORE_PROXY_ENV_NAME_STR: "env-key-source"},
        ):
            service = buildVerboseElasticIpPoolService(argumentNamespace)

        self.assertEqual(service.keyValStoreProxyStr, "env-key-source")


if __name__ == "__main__":
    unittest.main()
