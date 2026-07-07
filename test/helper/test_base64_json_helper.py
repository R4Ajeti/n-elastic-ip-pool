import base64
import json
import unittest

from n_elastic_ip_pool.helper.base64_json_helper import (
    decodeBase64JsonObject,
    decodeBase64JsonValue,
    parseJsonValue,
)


class Base64JsonHelperTest(unittest.TestCase):
    def testDecodeBase64JsonValueReturnsDecodedJson(self) -> None:
        payloadDict = {"project_id": "sample-project", "enabled": True}
        encodedValueStr = base64.b64encode(
            json.dumps(payloadDict).encode("utf-8"),
        ).decode("utf-8")

        resultValue = decodeBase64JsonValue(encodedValueStr)

        self.assertEqual(resultValue, payloadDict)

    def testDecodeBase64JsonObjectReturnsNoneForArrayPayload(self) -> None:
        encodedValueStr = base64.b64encode(b'["not", "an", "object"]').decode("utf-8")

        resultDict = decodeBase64JsonObject(encodedValueStr)

        self.assertIsNone(resultDict)

    def testDecodeBase64JsonValueSafelyHandlesMissingOrInvalidInput(self) -> None:
        self.assertIsNone(decodeBase64JsonValue(None))
        self.assertIsNone(decodeBase64JsonValue(""))
        self.assertIsNone(decodeBase64JsonValue("not-valid-base64"))
        self.assertIsNone(decodeBase64JsonValue(base64.b64encode(b"{bad").decode("utf-8")))

    def testParseJsonValueSafelyHandlesInvalidInput(self) -> None:
        self.assertEqual(parseJsonValue('{"ok": true}'), {"ok": True})
        self.assertIsNone(parseJsonValue("{bad"))
        self.assertIsNone(parseJsonValue(None))


if __name__ == "__main__":
    unittest.main()
