import unittest
from unittest.mock import patch

from n_elastic_ip_pool.constant.elastic_ip_pool_constant import PROXY_MAX_TIMING_MILLISECOND_INT
from n_elastic_ip_pool.proxy.elastic_ip_health_check_proxy import ElasticIpHealthCheckProxy


class FakeHttpResponse:
    def __init__(self, statusCodeInt: int = 200) -> None:
        self.statusCodeInt = statusCodeInt

    def __enter__(self) -> "FakeHttpResponse":
        return self

    def __exit__(self, excType, excValue, traceback) -> None:
        return None

    def read(self, sizeInt: int = -1) -> bytes:
        return b'{"ip":"198.51.100.10"}'

    def getcode(self) -> int:
        return self.statusCodeInt


class FakeOpener:
    def __init__(self, response=None, error=None) -> None:
        self.response = response
        self.error = error
        self.timeoutSecondInt = 0

    def open(self, request, timeout: int):
        self.timeoutSecondInt = timeout
        if self.error:
            raise self.error
        return self.response


class ElasticIpHealthCheckProxyTest(unittest.TestCase):
    def testTestProxyReturnsWorkingResult(self) -> None:
        fakeOpener = FakeOpener(FakeHttpResponse(200))

        with patch(
            "n_elastic_ip_pool.proxy.elastic_ip_health_check_proxy.build_opener",
            return_value=fakeOpener,
        ):
            resultDict = ElasticIpHealthCheckProxy(timeoutSecondInt=3).testProxy(
                "proxy-one.example.net:8080",
            )

        self.assertTrue(resultDict["isWorking"])
        self.assertEqual(resultDict["proxy"], "proxy-one.example.net:8080")
        self.assertEqual(resultDict["statusCode"], 200)
        self.assertIsNone(resultDict["error"])
        self.assertEqual(fakeOpener.timeoutSecondInt, 3)

    def testTestProxyHandlesTimeoutSafely(self) -> None:
        fakeOpener = FakeOpener(error=TimeoutError())

        with patch(
            "n_elastic_ip_pool.proxy.elastic_ip_health_check_proxy.build_opener",
            return_value=fakeOpener,
        ):
            resultDict = ElasticIpHealthCheckProxy().testProxy(
                "proxy-one.example.net:8080",
            )

        self.assertFalse(resultDict["isWorking"])
        self.assertEqual(resultDict["error"], "TimeoutError")
        self.assertIsNone(resultDict["statusCode"])
        self.assertEqual(
            fakeOpener.timeoutSecondInt,
            PROXY_MAX_TIMING_MILLISECOND_INT / 1000,
        )

    def testTestProxyUsesMillisecondTimeoutOverride(self) -> None:
        fakeOpener = FakeOpener(FakeHttpResponse(200))

        with patch(
            "n_elastic_ip_pool.proxy.elastic_ip_health_check_proxy.build_opener",
            return_value=fakeOpener,
        ):
            ElasticIpHealthCheckProxy(timeoutMillisecondInt=1500).testProxy(
                "proxy-one.example.net:8080",
            )

        self.assertEqual(fakeOpener.timeoutSecondInt, 1.5)

    def testTestProxyRejectsInvalidProxyFormatWithoutNetwork(self) -> None:
        with patch("n_elastic_ip_pool.proxy.elastic_ip_health_check_proxy.build_opener") as openerMock:
            resultDict = ElasticIpHealthCheckProxy().testProxy("not-a-proxy")

        self.assertFalse(resultDict["isWorking"])
        self.assertEqual(resultDict["error"], "invalid_proxy_format")
        openerMock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
