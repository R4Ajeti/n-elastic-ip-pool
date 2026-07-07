import unittest

from n_elastic_ip_pool.constant import elastic_ip_pool_constant


class ElasticIpPoolConstantTest(unittest.TestCase):
    def testConstantValueTypes(self) -> None:
        self.assertIsInstance(elastic_ip_pool_constant.CORE_LOGGER_NAME_STR, str)
        self.assertIsInstance(elastic_ip_pool_constant.LOGGER_LEVEL_ENV_NAME_STR, str)
        self.assertIsInstance(elastic_ip_pool_constant.DEFAULT_LOGGER_LEVEL_STR, str)
        self.assertIsInstance(elastic_ip_pool_constant.LOGGER_LEVEL_INFO_STR, str)
        self.assertIsInstance(elastic_ip_pool_constant.LOGGER_LEVEL_DEBUG_STR, str)
        self.assertIsInstance(
            elastic_ip_pool_constant.DEFAULT_PROXY_RELEASE_CHANNEL_STR,
            str,
        )
        self.assertIsInstance(
            elastic_ip_pool_constant.DEFAULT_PROXY_SELECTION_MODE_STR,
            str,
        )
        self.assertIsInstance(
            elastic_ip_pool_constant.DEFAULT_PROXY_RESULT_COUNT_INT,
            int,
        )
        self.assertIsInstance(
            elastic_ip_pool_constant.DEFAULT_PROXY_CANDIDATE_LIMIT_INT,
            int,
        )
        self.assertIsInstance(
            elastic_ip_pool_constant.DEFAULT_PROXY_SHUFFLE_CANDIDATE_BOOL,
            bool,
        )
        self.assertIsInstance(
            elastic_ip_pool_constant.DEFAULT_PROXY_USE_SAVED_PROXY_BOOL,
            bool,
        )
        self.assertIsInstance(
            elastic_ip_pool_constant.DEFAULT_PROXY_SAVE_WORKING_PROXY_BOOL,
            bool,
        )
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
        self.assertIsInstance(
            elastic_ip_pool_constant.PROXY_MAX_TIMING_MILLISECOND_INT,
            int,
        )
        self.assertIsInstance(
            elastic_ip_pool_constant.FIREBASE_DATABASE_TYPE_ENV_NAME_STR,
            str,
        )
        self.assertIsInstance(
            elastic_ip_pool_constant.FIREBASE_FIRESTORE_KEY_BASE64_ENV_NAME_STR,
            str,
        )
        self.assertIsInstance(
            elastic_ip_pool_constant.FIREBASE_REALTIME_DATABASE_KEY_BASE64_ENV_NAME_STR,
            str,
        )
        self.assertIsInstance(
            elastic_ip_pool_constant.FIREBASE_REALTIME_DATABASE_URL_ENV_NAME_STR,
            str,
        )
        self.assertIsInstance(
            elastic_ip_pool_constant.FIREBASE_DATABASE_TYPE_FIRESTORE_STR,
            str,
        )
        self.assertIsInstance(
            elastic_ip_pool_constant.FIREBASE_DATABASE_TYPE_REALTIME_DATABASE_STR,
            str,
        )
        self.assertIsInstance(
            elastic_ip_pool_constant.MAX_PROXY_USAGE_COUNT_INT,
            int,
        )
        self.assertIsInstance(
            elastic_ip_pool_constant.DEFAULT_FIREBASE_COLLECTION_NAME_STR,
            str,
        )
        self.assertIsInstance(
            elastic_ip_pool_constant.DEFAULT_FIREBASE_USAGE_HISTORY_PATH_STR,
            str,
        )


if __name__ == "__main__":
    unittest.main()
