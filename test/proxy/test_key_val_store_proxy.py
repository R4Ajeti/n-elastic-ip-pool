import unittest

from core.proxy.key_val_store_proxy import KeyValStoreProxy


class KeyValStoreProxyTest(unittest.TestCase):
    @unittest.skip("Placeholder until external key/value store abstraction is implemented.")
    def testSetValueReturnsNormalizedResult(self) -> None:
        resultDict = KeyValStoreProxy().setValue(
            "elastic-ip-pool/sample-resource",
            {"status": "active"},
        )

        self.assertTrue(resultDict["stored"])


if __name__ == "__main__":
    unittest.main()
