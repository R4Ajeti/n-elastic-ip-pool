import unittest

from core.helper.proxy_address_format_helper import (
    isProxyAddressFormatValid,
    normalizeProxyAddress,
)


class ProxyAddressFormatHelperTest(unittest.TestCase):
    def testNormalizeProxyAddressAcceptsHostPort(self) -> None:
        self.assertEqual(
            normalizeProxyAddress("Proxy-One.Example.Net:8080"),
            "proxy-one.example.net:8080",
        )

    def testNormalizeProxyAddressAcceptsHttpUrl(self) -> None:
        self.assertEqual(
            normalizeProxyAddress("http://proxy-one.example.net:8080"),
            "proxy-one.example.net:8080",
        )

    def testIsProxyAddressFormatValidRejectsCredentialUrl(self) -> None:
        self.assertFalse(
            isProxyAddressFormatValid("http://user:pass@proxy-one.example.net:8080"),
        )

    def testIsProxyAddressFormatValidRejectsInvalidPort(self) -> None:
        self.assertFalse(isProxyAddressFormatValid("proxy-one.example.net:70000"))


if __name__ == "__main__":
    unittest.main()
