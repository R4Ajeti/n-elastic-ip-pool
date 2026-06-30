import unittest
from unittest.mock import patch

from core.constant.elastic_ip_pool_constant import KEY_VAL_DUMMY_PROXY_VALUE_STR
from core.helper.string_hash_helper import hashStringValue
from core.service.verbose_elastic_ip_pool_service import VerboseElasticIpPoolService


class FakeKeyValStoreProxy:
    def __init__(self) -> None:
        self.valueStr = ""
        self.getKeyStr = ""
        self.setKeyStr = ""
        self.setValueStr = ""

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
            "stored": True,
            "value": valueStr,
            "response_value": valueStr,
            "status_code": 200,
        }

    def buildGetUrl(self, keyStr: str) -> str:
        return f"https://example.com/get/{keyStr}"

    def buildSetUrl(self, keyStr: str, valueStr: str) -> str:
        return f"https://example.com/set/{keyStr}/{valueStr}"


class VerboseElasticIpPoolServiceTest(unittest.TestCase):
    def testRunUsesConstructorKeySourceAndDummyProxyValue(self) -> None:
        keyValStoreProxy = FakeKeyValStoreProxy()
        service = VerboseElasticIpPoolService(
            keyValStoreProxyStr="custom-key-source",
            dummyProxyValueStr=KEY_VAL_DUMMY_PROXY_VALUE_STR,
            keyValStoreProxy=keyValStoreProxy,
        )
        expectedKeyStr = hashStringValue("custom-key-source")

        with patch("builtins.print"):
            resultStr = service.run()

        self.assertEqual(resultStr, KEY_VAL_DUMMY_PROXY_VALUE_STR)
        self.assertEqual(keyValStoreProxy.setKeyStr, expectedKeyStr)
        self.assertEqual(keyValStoreProxy.getKeyStr, expectedKeyStr)
        self.assertEqual(keyValStoreProxy.setValueStr, KEY_VAL_DUMMY_PROXY_VALUE_STR)


if __name__ == "__main__":
    unittest.main()
