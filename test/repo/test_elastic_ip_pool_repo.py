import unittest

from core.repo.elastic_ip_pool_repo import ElasticIpPoolRepo


class ElasticIpPoolRepoTest(unittest.TestCase):
    @unittest.skip("Placeholder until in-memory repo behavior is implemented.")
    def testListResourceReturnsStoredResource(self) -> None:
        repo = ElasticIpPoolRepo()

        self.assertEqual(repo.listResource(), [])


if __name__ == "__main__":
    unittest.main()
