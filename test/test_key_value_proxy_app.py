import os
import unittest
from unittest.mock import patch

from app.key_value_proxy_app import buildVerboseElasticIpPoolService
from n_elastic_ip_pool.constant.elastic_ip_pool_constant import (
    KEY_VAL_AUTH_TOKEN_ENV_NAME_STR,
    KEY_VAL_BASE_URL_ENV_NAME_STR,
    KEY_VAL_STORE_PROXY_ENV_NAME_STR,
    PROXY_MAX_TIMING_MILLISECOND_ENV_NAME_STR,
    PROXY_TEST_TARGET_URL_ENV_NAME_STR,
)


class KeyValueProxyAppTest(unittest.TestCase):
    def testBlankKeyValBaseUrlKeepsPersistenceDisabled(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            service = buildVerboseElasticIpPoolService("missing.env")

        self.assertFalse(service.useSavedProxyBool)
        self.assertFalse(service.saveWorkingProxyBool)
        self.assertEqual(service.proxyUsageHistoryRepo.databaseTypeStr, "")

    def testConfiguredKeyValProviderUsesNamespaceAndBearerToken(self) -> None:
        with patch.dict(
            os.environ,
            {
                KEY_VAL_BASE_URL_ENV_NAME_STR: "https://keyval.example.test/",
                KEY_VAL_AUTH_TOKEN_ENV_NAME_STR: "safe-test-token",
                KEY_VAL_STORE_PROXY_ENV_NAME_STR: "my-proxy-pool",
            },
            clear=True,
        ):
            service = buildVerboseElasticIpPoolService("missing.env")

        self.assertTrue(service.useSavedProxyBool)
        self.assertTrue(service.saveWorkingProxyBool)
        self.assertEqual(service.keyValStoreProxyStr, "my-proxy-pool")
        self.assertEqual(
            service.keyValStoreProxy.baseUrlStr,
            "https://keyval.example.test",
        )
        self.assertEqual(service.keyValStoreProxy.authTokenStr, "safe-test-token")

    def testProxyHealthCheckConfigurationComesFromEnvironment(self) -> None:
        with patch.dict(
            os.environ,
            {
                PROXY_TEST_TARGET_URL_ENV_NAME_STR: "https://target.example.test/ip",
                PROXY_MAX_TIMING_MILLISECOND_ENV_NAME_STR: "1250",
            },
            clear=True,
        ):
            service = buildVerboseElasticIpPoolService("missing.env")

        self.assertEqual(
            service.elasticIpHealthCheckProxy.targetUrlStr,
            "https://target.example.test/ip",
        )
        self.assertEqual(service.proxyMaxTimingMillisecondInt, 1250)
        self.assertEqual(service.elasticIpHealthCheckProxy.timeoutSecondFloat, 1.25)


if __name__ == "__main__":
    unittest.main()
