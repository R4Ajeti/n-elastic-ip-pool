import unittest

from n_elastic_ip_pool.helper.sensitive_value_redaction_helper import (
    formatNetworkLocationForLog,
    redactNetworkLocationValue,
    redactUrlPathValue,
)


class SensitiveValueRedactionHelperTest(unittest.TestCase):
    def testFormatNetworkLocationShowsAddressWithoutSecrets(self) -> None:
        for valueStr in (
            "proxy.example.net:8080",
            "http://sample-user:sample-password@proxy.example.net:8080/private?token=sample#secret",
            "sample-user:sample-password@proxy.example.net:8080",
        ):
            with self.subTest(value=valueStr):
                self.assertEqual(formatNetworkLocationForLog(valueStr), "proxy.example.net:8080")

    def testFormatNetworkLocationHidesInvalidValues(self) -> None:
        for value in (None, "secret-token", "http://[broken", "host.example:99999", "host.example:80\nsecret"):
            with self.subTest(value=value):
                self.assertEqual(formatNetworkLocationForLog(value), "[redacted]")

    def testRedactNetworkLocationValueHidesHostPortValues(self) -> None:
        resultStr = redactNetworkLocationValue(
            '["proxy-one.example.net:8080","192.0.2.10:1081"]',
        )

        self.assertEqual(
            resultStr,
            '["[redacted-network-location]","[redacted-network-location]"]',
        )

    def testRedactUrlPathValueHidesPublicCachePath(self) -> None:
        resultStr = redactUrlPathValue(
            "https://api.keyval.org/set/sample-key/%5B%22proxy-one.example.net%3A8080%22%5D",
        )

        self.assertEqual(resultStr, "https://api.keyval.org/[redacted]")


if __name__ == "__main__":
    unittest.main()
