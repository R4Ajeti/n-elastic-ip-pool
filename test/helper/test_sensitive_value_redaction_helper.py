import unittest

from n_elastic_ip_pool.helper.sensitive_value_redaction_helper import (
    redactNetworkLocationValue,
    redactUrlPathValue,
)


class SensitiveValueRedactionHelperTest(unittest.TestCase):
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
