from core.constant.elastic_ip_pool_constant import (
    KEY_VAL_DUMMY_PROXY_KEY_STR,
    KEY_VAL_STORE_PROXY_ENV_NAME_STR,
)
from core.helper.env_value_helper import getEnvValue
from core.service.verbose_elastic_ip_pool_service import VerboseElasticIpPoolService


def main() -> None:
    keyValStoreProxyStr = getEnvValue(
        KEY_VAL_STORE_PROXY_ENV_NAME_STR,
        KEY_VAL_DUMMY_PROXY_KEY_STR,
    )

    verboseElasticIpPoolService = VerboseElasticIpPoolService(
        keyValStoreProxyStr=keyValStoreProxyStr,
    )
    verboseElasticIpPoolService.run()
    
    print("Final selected proxy:", verboseElasticIpPoolService.finalValueStr)
    print("Ranked proxy list:", verboseElasticIpPoolService.rankedProxyList)


if __name__ == "__main__":
    main()
