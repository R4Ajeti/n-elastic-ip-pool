import unittest

from core.proxy.elastic_ip_health_check_proxy import ElasticIpHealthCheckProxy


class ElasticIpHealthCheckProxyTest(unittest.TestCase):
    @unittest.skip("Placeholder until external health-check abstraction is implemented.")
    def testCheckHealthReturnsNormalizedResult(self) -> None:
        proxyResourceDict = {
            "proxy_resource_id": "eip-sample-001",
            "ip_address": "203.0.113.10",
        }

        resultDict = ElasticIpHealthCheckProxy().checkHealth(proxyResourceDict)

        self.assertIn("is_working", resultDict)


if __name__ == "__main__":
    unittest.main()
