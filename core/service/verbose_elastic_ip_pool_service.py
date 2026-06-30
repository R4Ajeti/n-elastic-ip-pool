from core.constant.elastic_ip_pool_constant import (
    KEY_VAL_DUMMY_PROXY_KEY_STR,
    KEY_VAL_DUMMY_PROXY_VALUE_STR,
)
from core.proxy.key_val_store_proxy import KeyValStoreProxy
from core.service.elastic_ip_pool_service import ElasticIpPoolService


class VerboseElasticIpPoolService(ElasticIpPoolService):
    """Printable manual flow service for the KeyVal dummy proxy path."""

    def __init__(
        self,
        keyValStoreProxyStr: str = KEY_VAL_DUMMY_PROXY_KEY_STR,
        dummyProxyValueStr: str = KEY_VAL_DUMMY_PROXY_VALUE_STR,
        keyValStoreProxy: KeyValStoreProxy | None = None,
    ) -> None:
        super().__init__(
            keyValStoreProxy=keyValStoreProxy,
            keyValStoreProxyStr=keyValStoreProxyStr,
            dummyProxyValueStr=dummyProxyValueStr,
        )

    def run(self) -> str:
        keyValKeyHashStr = self.getKeyValDummyProxyKey()

        print("=== KeyVal dummy proxy manual run ===")
        print("KeyVal key source:", self.keyValStoreProxyStr)
        print("KeyVal hashed key:", keyValKeyHashStr)
        print("safe hardcoded dummy proxy value:", self.dummyProxyValueStr)
        print("KeyVal get URL:", self.keyValStoreProxy.buildGetUrl(keyValKeyHashStr))
        print(
            "KeyVal save URL:",
            self.keyValStoreProxy.buildSetUrl(
                keyValKeyHashStr,
                self.dummyProxyValueStr,
            ),
        )
        print("note: KeyVal is public, so use only safe dummy proxy values")

        print("=== force save hardcoded dummy proxy value ===")
        savedValueStr = self.update()
        print("[manual] saved value:", savedValueStr)

        print("=== service get flow ===")
        finalValueStr = self.get()

        print("=== final ===")
        print("stored KeyVal key:", keyValKeyHashStr)
        print("stored KeyVal value:", finalValueStr)
        print(
            "open this URL to read it:",
            self.keyValStoreProxy.buildGetUrl(keyValKeyHashStr),
        )

        return finalValueStr

    def get(self) -> str:
        print("[service.get] start")
        resultStr = super().get()
        print("[service.get] return:", resultStr)
        return resultStr

    def check(self) -> str | None:
        print("[service.check] checking KeyVal for existing dummy proxy")
        keyValKeyStr = self.getKeyValDummyProxyKey()
        print("[service.check] KeyVal key:", keyValKeyStr)
        print(
            "[service.check] KeyVal get URL:",
            self.keyValStoreProxy.buildGetUrl(keyValKeyStr),
        )
        resultDict = self.keyValStoreProxy.getValue(keyValKeyStr)
        print("[service.check] KeyVal result:", resultDict)

        if resultDict.get("exists") and resultDict.get("value"):
            resultStr = str(resultDict["value"])
            print("[service.check] found:", resultStr)
            return resultStr

        print("[service.check] found:", None)
        return None

    def update(self) -> str:
        print("[service.update] safe hardcoded dummy proxy:", self.dummyProxyValueStr)
        print("[service.update] hashing KeyVal key before save")
        keyValKeyStr = self.getKeyValDummyProxyKey()
        print("[service.update] KeyVal key:", keyValKeyStr)
        print(
            "[service.update] KeyVal save URL:",
            self.keyValStoreProxy.buildSetUrl(
                keyValKeyStr,
                self.dummyProxyValueStr,
            ),
        )
        resultDict = self.keyValStoreProxy.setValue(
            keyValKeyStr,
            self.dummyProxyValueStr,
        )
        print("[service.update] KeyVal result:", resultDict)

        if not resultDict.get("stored"):
            raise RuntimeError("Dummy proxy value was not stored in KeyVal.")

        resultStr = str(resultDict.get("value") or self.dummyProxyValueStr)
        print("[service.update] saved dummy proxy value:", resultStr)
        return resultStr
