from core.constant.elastic_ip_pool_constant import (
    KEY_VAL_DUMMY_PROXY_KEY_STR,
    KEY_VAL_DUMMY_PROXY_VALUE_STR,
    KEY_VAL_STORE_PROXY_ENV_NAME_STR,
)
from core.helper.env_value_helper import getEnvValue
from core.service.verbose_elastic_ip_pool_service import VerboseElasticIpPoolService


SAFE_HARDCODED_DUMMY_PROXY_STR = KEY_VAL_DUMMY_PROXY_VALUE_STR


def main() -> None:
    keyValStoreProxyStr = getEnvValue(
        KEY_VAL_STORE_PROXY_ENV_NAME_STR,
        KEY_VAL_DUMMY_PROXY_KEY_STR,
    )

    service = VerboseElasticIpPoolService(
        # keyValStoreProxyStr=keyValStoreProxyStr,
        # dummyProxyValueStr=SAFE_HARDCODED_DUMMY_PROXY_STR,
    )
    service.run()


if __name__ == "__main__":
    main()
