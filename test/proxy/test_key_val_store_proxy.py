import io
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from n_elastic_ip_pool.constant.elastic_ip_pool_constant import (
    DEFAULT_TIMEOUT_SECOND_INT,
    KEY_VAL_API_BASE_URL_STR,
    KEY_VAL_USER_AGENT_STR,
)
from n_elastic_ip_pool.proxy.key_val_store_proxy import KeyValStoreProxy


class FakeHttpResponse:
    def __init__(self, responseTextStr: str, statusCodeInt: int = 200) -> None:
        self.responseTextStr = responseTextStr
        self.statusCodeInt = statusCodeInt

    def __enter__(self) -> "FakeHttpResponse":
        return self

    def __exit__(self, excType, excValue, traceback) -> None:
        return None

    def read(self) -> bytes:
        return self.responseTextStr.encode("utf-8")

    def getcode(self) -> int:
        return self.statusCodeInt


class KeyValStoreProxyTest(unittest.TestCase):
    def testGetValueReturnsNormalizedExistingValue(self) -> None:
        with patch(
            "n_elastic_ip_pool.proxy.key_val_store_proxy.urlopen",
            return_value=FakeHttpResponse(
                '{"status":"SUCCESS","key":"sample-key","val":"stored-hash"}',
            ),
        ) as urlopenMock:
            resultDict = KeyValStoreProxy().getValue("sample-key")

        request = urlopenMock.call_args.args[0]
        self.assertEqual(
            request.full_url,
            f"{KEY_VAL_API_BASE_URL_STR}/get/sample-key",
        )
        self.assertEqual(request.get_method(), "GET")
        self.assertEqual(request.headers["User-agent"], KEY_VAL_USER_AGENT_STR)
        self.assertEqual(
            urlopenMock.call_args.kwargs["timeout"],
            DEFAULT_TIMEOUT_SECOND_INT,
        )
        self.assertEqual(
            resultDict,
            {
                "key": "sample-key",
                "exists": True,
                "value": "stored-hash",
                "status_code": 200,
            },
        )

    def testGetValueReturnsMissingForNotFound(self) -> None:
        notFoundError = HTTPError(
            "https://api.keyval.org/get/missing-key",
            404,
            "Not Found",
            None,
            io.BytesIO(b""),
        )

        with patch(
            "n_elastic_ip_pool.proxy.key_val_store_proxy.urlopen",
            side_effect=notFoundError,
        ):
            resultDict = KeyValStoreProxy().getValue("missing-key")
        notFoundError.close()

        self.assertEqual(
            resultDict,
            {
                "key": "missing-key",
                "exists": False,
                "value": None,
                "status_code": 404,
            },
        )

    def testSetValueReturnsNormalizedStoredValue(self) -> None:
        with patch(
            "n_elastic_ip_pool.proxy.key_val_store_proxy.urlopen",
            return_value=FakeHttpResponse(
                '{"status":"SUCCESS","key":"sample-key","val":"stored-hash"}',
            ),
        ) as urlopenMock:
            resultDict = KeyValStoreProxy().setValue("sample-key", "stored-hash")

        request = urlopenMock.call_args.args[0]
        self.assertEqual(
            request.full_url,
            f"{KEY_VAL_API_BASE_URL_STR}/set/sample-key/stored-hash",
        )
        self.assertEqual(request.get_method(), "GET")
        self.assertEqual(
            resultDict,
            {
                "key": "sample-key",
                "stored": True,
                "value": "stored-hash",
                "response_value": "stored-hash",
                "response_status": "SUCCESS",
                "status_code": 200,
            },
        )

    def testSetValueMarksProviderFailureAsNotStored(self) -> None:
        with patch(
            "n_elastic_ip_pool.proxy.key_val_store_proxy.urlopen",
            return_value=FakeHttpResponse(
                '{"status":"-KEY-OR-VALUE-TOO-LONG-"}',
            ),
        ):
            resultDict = KeyValStoreProxy().setValue("sample-key", '["proxy-one.example.net:8080"]')

        self.assertFalse(resultDict["stored"])
        self.assertEqual(resultDict["response_status"], "-KEY-OR-VALUE-TOO-LONG-")

    def testBuildSetUrlUrlEncodesProxyListJson(self) -> None:
        resultStr = KeyValStoreProxy().buildSetUrl(
            "sample-key",
            '["proxy-one.example.net:8080"]',
        )

        self.assertEqual(
            resultStr,
            f"{KEY_VAL_API_BASE_URL_STR}/set/sample-key/%5B%22proxy-one.example.net%3A8080%22%5D",
        )

    def testBuildSetUrlUrlEncodesEmptyProxyList(self) -> None:
        resultStr = KeyValStoreProxy().buildSetUrl("sample-key", "[]")

        self.assertEqual(
            resultStr,
            f"{KEY_VAL_API_BASE_URL_STR}/set/sample-key/%5B%5D",
        )


if __name__ == "__main__":
    unittest.main()
