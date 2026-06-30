import unittest

from core.proxy.elastic_ip_health_check_proxy import ElasticIpHealthCheckProxy
from core.proxy.key_val_store_proxy import KeyValStoreProxy
from core.repo.elastic_ip_pool_repo import ElasticIpPoolRepo
from core.service.elastic_ip_pool_service import ElasticIpPoolService


class ElasticIpPoolServiceTest(unittest.TestCase):
    @unittest.skip("Placeholder until Elastic IP pool selection rules are implemented.")
    def testGetAvailableResourceReturnsOnlyUsableResource(self) -> None:
        service = ElasticIpPoolService(
            ElasticIpPoolRepo(),
            ElasticIpHealthCheckProxy(),
            KeyValStoreProxy(),
        )

        resourceDict = service.getAvailableResource()

        self.assertIsNotNone(resourceDict)


if __name__ == "__main__":
    unittest.main()
