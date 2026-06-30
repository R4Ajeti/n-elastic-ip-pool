import unittest

from core.constant import elastic_ip_pool_constant


class ElasticIpPoolConstantTest(unittest.TestCase):
    def testConstantValueTypes(self) -> None:
        self.assertIsInstance(elastic_ip_pool_constant.CORE_LOGGER_NAME_STR, str)
        self.assertIsInstance(elastic_ip_pool_constant.DEFAULT_TIMEOUT_SECOND_INT, int)
        self.assertIsInstance(
            elastic_ip_pool_constant.MAX_ELASTIC_IP_FAILURE_COUNT_INT,
            int,
        )
        self.assertIsInstance(
            elastic_ip_pool_constant.ELASTIC_IP_HEALTH_CHECK_URL_STR,
            str,
        )
        self.assertIsInstance(
            elastic_ip_pool_constant.DEFAULT_PROXY_COUNTRY_CODE_STR,
            str,
        )
        self.assertIsInstance(
            elastic_ip_pool_constant.PROXY_SCRAPE_API_BASE_URL_STR,
            str,
        )
        self.assertIsInstance(
            elastic_ip_pool_constant.PROXY_SCRAPE_TIMEOUT_MILLISECOND_INT,
            int,
        )
        self.assertIsInstance(
            elastic_ip_pool_constant.PROXY_TEST_TARGET_URL_STR,
            str,
        )
        self.assertIsInstance(
            elastic_ip_pool_constant.PROXY_VALIDATION_SUCCESS_COUNT_INT,
            int,
        )


if __name__ == "__main__":
    unittest.main()
