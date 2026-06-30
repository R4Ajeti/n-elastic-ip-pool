import unittest

from core.constant.elastic_ip_pool_constant import (
    KEY_VAL_DUMMY_PROXY_HASH_SOURCE_STR,
    KEY_VAL_DUMMY_PROXY_KEY_STR,
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
    def testGetReturnsExistingStoredDummyProxyHash(self) -> None:
        keyValStoreProxy = FakeKeyValStoreProxy(
            {
                "key": KEY_VAL_DUMMY_PROXY_KEY_STR,
                "exists": True,
                "value": "existing-hash",
                "status_code": 200,
            },
        )
        service = ElasticIpPoolService(keyValStoreProxy=keyValStoreProxy)

        resultStr = service.get()

        self.assertEqual(resultStr, "existing-hash")
        self.assertEqual(keyValStoreProxy.getKeyStr, KEY_VAL_DUMMY_PROXY_KEY_STR)
        self.assertEqual(keyValStoreProxy.setValueCallCountInt, 0)

    def testGetUpdatesMissingDummyProxyHash(self) -> None:
        keyValStoreProxy = FakeKeyValStoreProxy(
            {
                "key": KEY_VAL_DUMMY_PROXY_KEY_STR,
                "exists": False,
                "value": None,
                "status_code": 404,
            },
        )
        service = ElasticIpPoolService(keyValStoreProxy=keyValStoreProxy)
        expectedHashStr = hashStringValue(KEY_VAL_DUMMY_PROXY_HASH_SOURCE_STR)

        resultStr = service.get()

        self.assertEqual(resultStr, expectedHashStr)
        self.assertEqual(keyValStoreProxy.setKeyStr, KEY_VAL_DUMMY_PROXY_KEY_STR)
        self.assertEqual(keyValStoreProxy.setValueStr, expectedHashStr)
        self.assertNotEqual(
            keyValStoreProxy.setValueStr,
            KEY_VAL_DUMMY_PROXY_HASH_SOURCE_STR,
        )

    def testCheckReturnsNoneWhenStoredDummyProxyMissing(self) -> None:
        keyValStoreProxy = FakeKeyValStoreProxy(
            {
                "key": KEY_VAL_DUMMY_PROXY_KEY_STR,
                "exists": False,
                "value": None,
                "status_code": 404,
            },
        )
        service = ElasticIpPoolService(keyValStoreProxy=keyValStoreProxy)

        self.assertIsNone(service.check())

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
