from core.proxy.elastic_ip_health_check_proxy import ElasticIpHealthCheckProxy
from core.proxy.key_val_store_proxy import KeyValStoreProxy
from core.repo.elastic_ip_pool_repo import ElasticIpPoolRepo


class ElasticIpPoolService:
    """Placeholder service for future Elastic IP pool business rules."""

    def __init__(
        self,
        elasticIpPoolRepo: ElasticIpPoolRepo,
        elasticIpHealthCheckProxy: ElasticIpHealthCheckProxy,
        keyValStoreProxy: KeyValStoreProxy,
    ) -> None:
        self.elasticIpPoolRepo = elasticIpPoolRepo
        self.elasticIpHealthCheckProxy = elasticIpHealthCheckProxy
        self.keyValStoreProxy = keyValStoreProxy

    def getAvailableResource(self) -> dict | None:
        """Select a usable proxy/IP resource once business rules are implemented."""
        raise NotImplementedError("Elastic IP pool selection is not implemented yet.")

    def markResourceFailed(self, resourceIdStr: str) -> None:
        """Record a failed proxy/IP resource once business rules are implemented."""
        raise NotImplementedError("Elastic IP pool failure handling is not implemented yet.")
