from core.constant.elastic_ip_pool_constant import (
    KEY_VAL_AUTH_TOKEN_ENV_NAME_STR,
    KEY_VAL_BASE_URL_ENV_NAME_STR,
    KEY_VAL_DUMMY_PROXY_KEY_STR,
    KEY_VAL_STORE_PROXY_ENV_NAME_STR,
    PROXY_MAX_TIMING_MILLISECOND_ENV_NAME_STR,
    PROXY_MAX_TIMING_MILLISECOND_INT,
    PROXY_TEST_TARGET_URL_ENV_NAME_STR,
    PROXY_TEST_TARGET_URL_STR,
)
from core.helper.env_value_helper import getEnvIntValue, getEnvValue
from core.proxy.elastic_ip_health_check_proxy import ElasticIpHealthCheckProxy
from core.proxy.key_val_store_proxy import KeyValStoreProxy
from core.service.verbose_elastic_ip_pool_service import VerboseElasticIpPoolService


def buildVerboseElasticIpPoolService(
    envFilePathStr: str = ".env",
) -> VerboseElasticIpPoolService:
    keyValStoreProxyStr = getEnvValue(
        KEY_VAL_STORE_PROXY_ENV_NAME_STR,
        KEY_VAL_DUMMY_PROXY_KEY_STR,
        envFilePathStr,
    )
    keyValBaseUrlStr = getEnvValue(
        KEY_VAL_BASE_URL_ENV_NAME_STR,
        "",
        envFilePathStr,
    )
    keyValAuthTokenStr = getEnvValue(
        KEY_VAL_AUTH_TOKEN_ENV_NAME_STR,
        "",
        envFilePathStr,
    )
    proxyTestTargetUrlStr = getEnvValue(
        PROXY_TEST_TARGET_URL_ENV_NAME_STR,
        PROXY_TEST_TARGET_URL_STR,
        envFilePathStr,
    )
    proxyMaxTimingMillisecondInt = max(
        1,
        getEnvIntValue(
            PROXY_MAX_TIMING_MILLISECOND_ENV_NAME_STR,
            PROXY_MAX_TIMING_MILLISECOND_INT,
            envFilePathStr,
        ),
    )

    keyValStoreProxy = None
    if keyValBaseUrlStr:
        keyValStoreProxy = KeyValStoreProxy(
            baseUrlStr=keyValBaseUrlStr,
            authTokenStr=keyValAuthTokenStr,
        )

    return VerboseElasticIpPoolService(
        keyValStoreProxyStr=keyValStoreProxyStr,
        keyValStoreProxy=keyValStoreProxy,
        elasticIpHealthCheckProxy=ElasticIpHealthCheckProxy(
            targetUrlStr=proxyTestTargetUrlStr,
            timeoutMillisecondInt=proxyMaxTimingMillisecondInt,
        ),
        proxyMaxTimingMillisecondInt=proxyMaxTimingMillisecondInt,
    )


def main() -> None:
    verboseElasticIpPoolService = buildVerboseElasticIpPoolService()
    verboseElasticIpPoolService.run()

    print("Final selected proxy:", verboseElasticIpPoolService.finalValueStr)
    print("Ranked proxy list:", verboseElasticIpPoolService.rankedProxyList)


if __name__ == "__main__":
    main()
