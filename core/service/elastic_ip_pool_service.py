from core.constant.elastic_ip_pool_constant import (
    KEY_VAL_DUMMY_PROXY_KEY_STR,
    KEY_VAL_DUMMY_PROXY_VALUE_STR,
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
        keyValStoreProxyStr: str = KEY_VAL_DUMMY_PROXY_KEY_STR,
        dummyProxyValueStr: str = KEY_VAL_DUMMY_PROXY_VALUE_STR,
    ) -> None:
        self.elasticIpPoolRepo = elasticIpPoolRepo or ElasticIpPoolRepo()
        self.elasticIpHealthCheckProxy = (
            elasticIpHealthCheckProxy or ElasticIpHealthCheckProxy()
        )
        self.keyValStoreProxy = keyValStoreProxy or KeyValStoreProxy()
        self.keyValStoreProxyStr = keyValStoreProxyStr
        self.dummyProxyValueStr = dummyProxyValueStr

    def get(self) -> str:
        storedProxyValueStr = self.check()
        if storedProxyValueStr:
            return storedProxyValueStr

        return self.update()

    def check(self) -> str | None:
        keyValKeyStr = self.getKeyValDummyProxyKey()
        resultDict = self.keyValStoreProxy.getValue(keyValKeyStr)
        if resultDict.get("exists") and resultDict.get("value"):
            return str(resultDict["value"])

        return None

    def update(self) -> str:
        keyValKeyStr = self.getKeyValDummyProxyKey()
        resultDict = self.keyValStoreProxy.setValue(
            keyValKeyStr,
            self.dummyProxyValueStr,
        )

        if not resultDict.get("stored"):
            raise RuntimeError("Dummy proxy value was not stored in KeyVal.")

        return str(resultDict.get("value") or self.dummyProxyValueStr)

    def getKeyValDummyProxyKey(self) -> str:
        return hashStringValue(self.keyValStoreProxyStr)

    def getAvailableResource(self) -> dict | None:
        """Select a usable proxy/IP resource once business rules are implemented."""
        raise NotImplementedError("Elastic IP pool selection is not implemented yet.")

    def markResourceFailed(self, resourceIdStr: str) -> None:
        """Record a failed proxy/IP resource once business rules are implemented."""
        raise NotImplementedError("Elastic IP pool failure handling is not implemented yet.")
