import unittest

from core.helper.ip_address_format_helper import isIpAddressFormatValid


class IpAddressFormatHelperTest(unittest.TestCase):
    @unittest.skip("Placeholder until generic IP address format validation is implemented.")
    def testIsIpAddressFormatValidAcceptsDocumentationIp(self) -> None:
        self.assertTrue(isIpAddressFormatValid("203.0.113.10"))

    @unittest.skip("Placeholder until generic IP address format validation is implemented.")
    def testIsIpAddressFormatValidRejectsInvalidText(self) -> None:
        self.assertFalse(isIpAddressFormatValid("not-an-ip-address"))


if __name__ == "__main__":
    unittest.main()
