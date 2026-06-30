import unittest

from core.helper.ip_address_format_helper import isIpAddressFormatValid
from core.helper.string_hash_helper import hashStringValue


class IpAddressFormatHelperTest(unittest.TestCase):
    @unittest.skip("Placeholder until generic IP address format validation is implemented.")
    def testIsIpAddressFormatValidAcceptsDocumentationIp(self) -> None:
        self.assertTrue(isIpAddressFormatValid("203.0.113.10"))

    @unittest.skip("Placeholder until generic IP address format validation is implemented.")
    def testIsIpAddressFormatValidRejectsInvalidText(self) -> None:
        self.assertFalse(isIpAddressFormatValid("not-an-ip-address"))


class StringHashHelperTest(unittest.TestCase):
    def testHashStringValueReturnsDeterministicHash(self) -> None:
        firstHashStr = hashStringValue("safe-dummy-value")
        secondHashStr = hashStringValue("safe-dummy-value")

        self.assertEqual(firstHashStr, secondHashStr)
        self.assertEqual(len(firstHashStr), 64)
        self.assertNotEqual(firstHashStr, "safe-dummy-value")

    def testHashStringValueRejectsNonStringValue(self) -> None:
        with self.assertRaises(TypeError):
            hashStringValue(123)


if __name__ == "__main__":
    unittest.main()
