import unittest

from core.constant.elastic_ip_pool_constant import (
    KEY_VAL_DUMMY_PROXY_KEY_STR,
    KEY_VAL_DUMMY_PROXY_VALUE_STR,
)
from core.helper.string_hash_helper import hashStringValue
from core.proxy.elastic_ip_health_check_proxy import ElasticIpHealthCheckProxy
from core.proxy.key_val_store_proxy import KeyValStoreProxy
from core.repo.elastic_ip_pool_repo import ElasticIpPoolRepo
from core.service.elastic_ip_pool_service import ElasticIpPoolService


class FakeKeyValStoreProxy:
    def __init__(self, getResultDict: dict) -> None:
        self.getResultDict = getResultDict
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
            "stored": True,
            "value": valueStr,
            "response_value": valueStr,
            "status_code": 200,
        }


class ElasticIpPoolServiceTest(unittest.TestCase):
    def testGetReturnsExistingStoredDummyProxyValue(self) -> None:
        expectedKeyStr = hashStringValue(KEY_VAL_DUMMY_PROXY_KEY_STR)
        keyValStoreProxy = FakeKeyValStoreProxy(
            {
                "key": expectedKeyStr,
                "exists": True,
                "value": "123.4.5.6:6666",
                "status_code": 200,
            },
        )
        service = ElasticIpPoolService(keyValStoreProxy=keyValStoreProxy)

        resultStr = service.get()

        self.assertEqual(resultStr, "123.4.5.6:6666")
        self.assertEqual(keyValStoreProxy.getKeyStr, expectedKeyStr)
        self.assertEqual(keyValStoreProxy.setValueCallCountInt, 0)

    def testGetUpdatesMissingDummyProxyValueAtHashedKey(self) -> None:
        expectedKeyStr = hashStringValue(KEY_VAL_DUMMY_PROXY_KEY_STR)
        keyValStoreProxy = FakeKeyValStoreProxy(
            {
                "key": expectedKeyStr,
                "exists": False,
                "value": None,
                "status_code": 404,
            },
        )
        service = ElasticIpPoolService(keyValStoreProxy=keyValStoreProxy)

        resultStr = service.get()

        self.assertEqual(resultStr, KEY_VAL_DUMMY_PROXY_VALUE_STR)
        self.assertEqual(keyValStoreProxy.setKeyStr, expectedKeyStr)
        self.assertEqual(keyValStoreProxy.setValueStr, KEY_VAL_DUMMY_PROXY_VALUE_STR)
        self.assertNotEqual(keyValStoreProxy.setKeyStr, KEY_VAL_DUMMY_PROXY_KEY_STR)

    def testCheckReturnsNoneWhenStoredDummyProxyMissing(self) -> None:
        expectedKeyStr = hashStringValue(KEY_VAL_DUMMY_PROXY_KEY_STR)
        keyValStoreProxy = FakeKeyValStoreProxy(
            {
                "key": expectedKeyStr,
                "exists": False,
                "value": None,
                "status_code": 404,
            },
        )
        service = ElasticIpPoolService(keyValStoreProxy=keyValStoreProxy)

        self.assertIsNone(service.check())

    def testUpdateStoresCustomDummyProxyValueAtHashedKey(self) -> None:
        expectedKeyStr = hashStringValue(KEY_VAL_DUMMY_PROXY_KEY_STR)
        keyValStoreProxy = FakeKeyValStoreProxy(
            {
                "key": expectedKeyStr,
                "exists": False,
                "value": None,
                "status_code": 404,
            },
        )
        service = ElasticIpPoolService(
            keyValStoreProxy=keyValStoreProxy,
            dummyProxyValueStr="http://203.0.113.10:8080",
        )

        resultStr = service.update()

        self.assertEqual(resultStr, "http://203.0.113.10:8080")
        self.assertEqual(keyValStoreProxy.setKeyStr, expectedKeyStr)
        self.assertEqual(keyValStoreProxy.setValueStr, "http://203.0.113.10:8080")

    def testUpdateUsesCustomKeyValStoreProxySourceString(self) -> None:
        expectedKeyStr = hashStringValue("custom-key-source")
        keyValStoreProxy = FakeKeyValStoreProxy(
            {
                "key": expectedKeyStr,
                "exists": False,
                "value": None,
                "status_code": 404,
            },
        )
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
