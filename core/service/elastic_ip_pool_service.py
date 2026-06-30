from core.constant.elastic_ip_pool_constant import (
    KEY_VAL_DUMMY_PROXY_HASH_SOURCE_STR,
    KEY_VAL_DUMMY_PROXY_KEY_STR,
)
from core.helper.string_hash_helper import hashStringValue
from core.proxy.elastic_ip_health_check_proxy import ElasticIpHealthCheckProxy
from core.proxy.key_val_store_proxy import KeyValStoreProxy
from core.repo.elastic_ip_pool_repo import ElasticIpPoolRepo


class ElasticIpPoolService:
    """Service for Elastic IP pool business rules."""

    def __init__(
        self,
        elasticIpPoolRepo: ElasticIpPoolRepo | None = None,
        elasticIpHealthCheckProxy: ElasticIpHealthCheckProxy | None = None,
        keyValStoreProxy: KeyValStoreProxy | None = None,
    ) -> None:
        self.elasticIpPoolRepo = elasticIpPoolRepo or ElasticIpPoolRepo()
        self.elasticIpHealthCheckProxy = (
            elasticIpHealthCheckProxy or ElasticIpHealthCheckProxy()
        )
        self.keyValStoreProxy = keyValStoreProxy or KeyValStoreProxy()

    def get(self) -> str:
        storedProxyValueStr = self.check()
        if storedProxyValueStr:
            return storedProxyValueStr

        return self.update()

    def check(self) -> str | None:
        resultDict = self.keyValStoreProxy.getValue(KEY_VAL_DUMMY_PROXY_KEY_STR)
        if resultDict.get("exists") and resultDict.get("value"):
            return str(resultDict["value"])

        return None

    def update(self) -> str:
        hashedProxyValueStr = hashStringValue(KEY_VAL_DUMMY_PROXY_HASH_SOURCE_STR)
        resultDict = self.keyValStoreProxy.setValue(
            KEY_VAL_DUMMY_PROXY_KEY_STR,
            hashedProxyValueStr,
        )

        if not resultDict.get("stored"):
            raise RuntimeError("Dummy proxy value was not stored in KeyVal.")

        return str(resultDict.get("value") or hashedProxyValueStr)

    def getAvailableResource(self) -> dict | None:
        """Select a usable proxy/IP resource once business rules are implemented."""
        raise NotImplementedError("Elastic IP pool selection is not implemented yet.")

    def markResourceFailed(self, resourceIdStr: str) -> None:
        """Record a failed proxy/IP resource once business rules are implemented."""
        raise NotImplementedError("Elastic IP pool failure handling is not implemented yet.")
