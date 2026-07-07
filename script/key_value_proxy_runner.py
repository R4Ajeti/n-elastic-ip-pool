import argparse

from n_elastic_ip_pool.constant.elastic_ip_pool_constant import (
    DEFAULT_PROXY_CANDIDATE_LIMIT_INT,
    DEFAULT_PROXY_RELEASE_CHANNEL_STR,
    DEFAULT_PROXY_RESULT_COUNT_INT,
    DEFAULT_PROXY_SAVE_WORKING_PROXY_BOOL,
    DEFAULT_PROXY_SELECTION_MODE_STR,
    DEFAULT_PROXY_SHUFFLE_CANDIDATE_BOOL,
    DEFAULT_PROXY_USE_SAVED_PROXY_BOOL,
    DEFAULT_TIMEOUT_SECOND_INT,
    KEY_VAL_API_BASE_URL_STR,
    KEY_VAL_DUMMY_PROXY_KEY_STR,
    KEY_VAL_STORE_PROXY_ENV_NAME_STR,
    LOGGER_LEVEL_DEBUG_STR,
    LOGGER_LEVEL_INFO_STR,
    PROXY_MAX_TIMING_MILLISECOND_INT,
    PROXY_RELEASE_CHANNEL_BETA_STR,
    PROXY_RELEASE_CHANNEL_CANARY_STR,
    PROXY_RELEASE_CHANNEL_STABLE_STR,
    PROXY_SCRAPE_ANONYMITY_FILTER_STR,
    PROXY_SCRAPE_API_BASE_URL_STR,
    PROXY_SCRAPE_COUNTRY_FILTER_STR,
    PROXY_SCRAPE_PROXY_TYPE_STR,
    PROXY_SCRAPE_REQUEST_VALUE_STR,
    PROXY_SCRAPE_SSL_FILTER_STR,
    PROXY_SCRAPE_TIMEOUT_MILLISECOND_INT,
    PROXY_SELECTION_MODE_FASTEST_STR,
    PROXY_SELECTION_MODE_RANDOM_STR,
    PROXY_TEST_TARGET_URL_STR,
    PROXY_VALIDATION_SUCCESS_COUNT_INT,
)
from n_elastic_ip_pool.helper.env_value_helper import getEnvValue
from n_elastic_ip_pool.proxy.elastic_ip_health_check_proxy import ElasticIpHealthCheckProxy
from n_elastic_ip_pool.proxy.geonode_free_proxy_list_proxy import GeonodeFreeProxyListProxy
from n_elastic_ip_pool.proxy.key_val_store_proxy import KeyValStoreProxy
from n_elastic_ip_pool.proxy.proxy_scrape_proxy import ProxyScrapeProxy
from n_elastic_ip_pool.service.verbose_elastic_ip_pool_service import VerboseElasticIpPoolService


def buildArgumentParser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a configurable verbose proxy discovery flow.",
    )
    parser.add_argument(
        "--release-channel",
        dest="releaseChannelStr",
        choices=[
            PROXY_RELEASE_CHANNEL_STABLE_STR,
            PROXY_RELEASE_CHANNEL_BETA_STR,
            PROXY_RELEASE_CHANNEL_CANARY_STR,
        ],
        default=DEFAULT_PROXY_RELEASE_CHANNEL_STR,
        help="Preset for validation strictness and randomness.",
    )
    parser.add_argument(
        "--key-source",
        dest="keyValStoreProxyStr",
        default=None,
        help="Source string hashed into the KeyVal storage key.",
    )
    parser.add_argument(
        "--log-level",
        dest="loggerLevelStr",
        choices=[LOGGER_LEVEL_INFO_STR, LOGGER_LEVEL_DEBUG_STR],
        default=None,
        help="Override LOGGER for this run.",
    )
    parser.add_argument(
        "--count",
        dest="proxyResultCountInt",
        type=int,
        default=None,
        help="Maximum working proxies to keep, rank, and save. Use 0 for all.",
    )
    parser.add_argument(
        "--selection-mode",
        dest="proxySelectionModeStr",
        choices=[PROXY_SELECTION_MODE_FASTEST_STR, PROXY_SELECTION_MODE_RANDOM_STR],
        default=None,
        help="Choose the fastest working proxy or a random working proxy.",
    )
    parser.add_argument(
        "--candidate-limit",
        dest="proxyCandidateLimitInt",
        type=int,
        default=None,
        help="Maximum normalized candidates to validate. Use 0 for all.",
    )
    parser.add_argument(
        "--shuffle-candidates",
        dest="proxyShuffleCandidateBool",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Shuffle normalized candidates before validation.",
    )
    parser.add_argument(
        "--random-seed",
        dest="proxyRandomSeedInt",
        type=int,
        default=None,
        help="Seed candidate shuffle and random selection for repeatable runs.",
    )
    parser.add_argument(
        "--validation-count",
        dest="proxyValidationSuccessCountInt",
        type=int,
        default=None,
        help="Successful health-check passes required before a proxy is usable.",
    )
    parser.add_argument(
        "--max-timing-ms",
        dest="proxyMaxTimingMillisecondInt",
        type=int,
        default=None,
        help="Reject proxies slower than this health-check timing.",
    )
    parser.add_argument(
        "--cache",
        dest="useSavedProxyBool",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Use saved KeyVal proxies before discovery. Use --no-cache to force search.",
    )
    parser.add_argument(
        "--save",
        dest="saveWorkingProxyBool",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Save working proxies to KeyVal. Use --no-save for read-only runs.",
    )
    parser.add_argument(
        "--provider-base-url",
        dest="proxyScrapeBaseUrlStr",
        default=None,
        help="ProxyScrape-compatible base URL.",
    )
    parser.add_argument(
        "--provider-timeout-ms",
        dest="proxyScrapeTimeoutMillisecondInt",
        type=int,
        default=None,
        help="ProxyScrape timeout query parameter in milliseconds.",
    )
    parser.add_argument(
        "--provider-timeout-second",
        dest="providerTimeoutSecondInt",
        type=int,
        default=None,
        help="Network timeout for ProxyScrape, Geonode, and KeyVal requests.",
    )
    parser.add_argument(
        "--country",
        dest="countryFilterStr",
        default=None,
        help="ProxyScrape country filter, such as all or US.",
    )
    parser.add_argument(
        "--proxy-type",
        dest="proxyTypeStr",
        default=None,
        help="ProxyScrape proxytype filter, such as all, http, socks4, or socks5.",
    )
    parser.add_argument(
        "--ssl",
        dest="sslFilterStr",
        default=None,
        help="ProxyScrape ssl filter, such as yes, no, or all when supported.",
    )
    parser.add_argument(
        "--anonymity",
        dest="anonymityFilterStr",
        default=None,
        help="ProxyScrape anonymity filter, such as elite, anonymous, transparent, or all.",
    )
    parser.add_argument(
        "--target-url",
        dest="targetUrlStr",
        default=None,
        help="Health-check target URL used by ElasticIpHealthCheckProxy.",
    )
    parser.add_argument(
        "--keyval-base-url",
        dest="keyValBaseUrlStr",
        default=None,
        help="KeyVal-compatible base URL.",
    )
    return parser


def buildReleaseChannelOptionDict(releaseChannelStr: str) -> dict:
    normalizedReleaseChannelStr = str(
        releaseChannelStr or DEFAULT_PROXY_RELEASE_CHANNEL_STR,
    ).lower()
    if normalizedReleaseChannelStr == PROXY_RELEASE_CHANNEL_BETA_STR:
        return {
            "releaseChannelStr": PROXY_RELEASE_CHANNEL_BETA_STR,
            "proxyResultCountInt": 3,
            "proxySelectionModeStr": PROXY_SELECTION_MODE_RANDOM_STR,
            "proxyCandidateLimitInt": 200,
            "proxyShuffleCandidateBool": True,
            "proxyValidationSuccessCountInt": PROXY_VALIDATION_SUCCESS_COUNT_INT,
            "proxyMaxTimingMillisecondInt": 2500,
            "useSavedProxyBool": DEFAULT_PROXY_USE_SAVED_PROXY_BOOL,
            "saveWorkingProxyBool": DEFAULT_PROXY_SAVE_WORKING_PROXY_BOOL,
        }

    if normalizedReleaseChannelStr == PROXY_RELEASE_CHANNEL_CANARY_STR:
        return {
            "releaseChannelStr": PROXY_RELEASE_CHANNEL_CANARY_STR,
            "proxyResultCountInt": 5,
            "proxySelectionModeStr": PROXY_SELECTION_MODE_RANDOM_STR,
            "proxyCandidateLimitInt": 500,
            "proxyShuffleCandidateBool": True,
            "proxyValidationSuccessCountInt": 2,
            "proxyMaxTimingMillisecondInt": 3500,
            "useSavedProxyBool": DEFAULT_PROXY_USE_SAVED_PROXY_BOOL,
            "saveWorkingProxyBool": DEFAULT_PROXY_SAVE_WORKING_PROXY_BOOL,
        }

    return {
        "releaseChannelStr": PROXY_RELEASE_CHANNEL_STABLE_STR,
        "proxyResultCountInt": DEFAULT_PROXY_RESULT_COUNT_INT,
        "proxySelectionModeStr": DEFAULT_PROXY_SELECTION_MODE_STR,
        "proxyCandidateLimitInt": DEFAULT_PROXY_CANDIDATE_LIMIT_INT,
        "proxyShuffleCandidateBool": DEFAULT_PROXY_SHUFFLE_CANDIDATE_BOOL,
        "proxyValidationSuccessCountInt": PROXY_VALIDATION_SUCCESS_COUNT_INT,
        "proxyMaxTimingMillisecondInt": PROXY_MAX_TIMING_MILLISECOND_INT,
        "useSavedProxyBool": DEFAULT_PROXY_USE_SAVED_PROXY_BOOL,
        "saveWorkingProxyBool": DEFAULT_PROXY_SAVE_WORKING_PROXY_BOOL,
    }


def buildRunOptionDict(argumentNamespace: argparse.Namespace) -> dict:
    releaseChannelOptionDict = buildReleaseChannelOptionDict(
        argumentNamespace.releaseChannelStr,
    )
    keyValStoreProxyStr = argumentNamespace.keyValStoreProxyStr or getEnvValue(
        KEY_VAL_STORE_PROXY_ENV_NAME_STR,
        KEY_VAL_DUMMY_PROXY_KEY_STR,
    )

    return {
        "releaseChannelStr": releaseChannelOptionDict["releaseChannelStr"],
        "keyValStoreProxyStr": keyValStoreProxyStr,
        "loggerLevelStr": argumentNamespace.loggerLevelStr,
        "proxyResultCountInt": resolveOption(
            argumentNamespace.proxyResultCountInt,
            releaseChannelOptionDict["proxyResultCountInt"],
        ),
        "proxySelectionModeStr": resolveOption(
            argumentNamespace.proxySelectionModeStr,
            releaseChannelOptionDict["proxySelectionModeStr"],
        ),
        "proxyCandidateLimitInt": resolveOption(
            argumentNamespace.proxyCandidateLimitInt,
            releaseChannelOptionDict["proxyCandidateLimitInt"],
        ),
        "proxyShuffleCandidateBool": resolveOption(
            argumentNamespace.proxyShuffleCandidateBool,
            releaseChannelOptionDict["proxyShuffleCandidateBool"],
        ),
        "proxyRandomSeedInt": argumentNamespace.proxyRandomSeedInt,
        "proxyValidationSuccessCountInt": resolveOption(
            argumentNamespace.proxyValidationSuccessCountInt,
            releaseChannelOptionDict["proxyValidationSuccessCountInt"],
        ),
        "proxyMaxTimingMillisecondInt": resolveOption(
            argumentNamespace.proxyMaxTimingMillisecondInt,
            releaseChannelOptionDict["proxyMaxTimingMillisecondInt"],
        ),
        "useSavedProxyBool": resolveOption(
            argumentNamespace.useSavedProxyBool,
            releaseChannelOptionDict["useSavedProxyBool"],
        ),
        "saveWorkingProxyBool": resolveOption(
            argumentNamespace.saveWorkingProxyBool,
            releaseChannelOptionDict["saveWorkingProxyBool"],
        ),
        "proxyScrapeBaseUrlStr": resolveOption(
            argumentNamespace.proxyScrapeBaseUrlStr,
            PROXY_SCRAPE_API_BASE_URL_STR,
        ),
        "proxyScrapeTimeoutMillisecondInt": resolveOption(
            argumentNamespace.proxyScrapeTimeoutMillisecondInt,
            PROXY_SCRAPE_TIMEOUT_MILLISECOND_INT,
        ),
        "providerTimeoutSecondInt": resolveOption(
            argumentNamespace.providerTimeoutSecondInt,
            DEFAULT_TIMEOUT_SECOND_INT,
        ),
        "countryFilterStr": resolveOption(
            argumentNamespace.countryFilterStr,
            PROXY_SCRAPE_COUNTRY_FILTER_STR,
        ),
        "proxyTypeStr": resolveOption(
            argumentNamespace.proxyTypeStr,
            PROXY_SCRAPE_PROXY_TYPE_STR,
        ),
        "sslFilterStr": resolveOption(
            argumentNamespace.sslFilterStr,
            PROXY_SCRAPE_SSL_FILTER_STR,
        ),
        "anonymityFilterStr": resolveOption(
            argumentNamespace.anonymityFilterStr,
            PROXY_SCRAPE_ANONYMITY_FILTER_STR,
        ),
        "targetUrlStr": resolveOption(
            argumentNamespace.targetUrlStr,
            PROXY_TEST_TARGET_URL_STR,
        ),
        "keyValBaseUrlStr": resolveOption(
            argumentNamespace.keyValBaseUrlStr,
            KEY_VAL_API_BASE_URL_STR,
        ),
    }


def resolveOption(value, defaultValue):
    if value is None:
        return defaultValue

    return value


def buildVerboseElasticIpPoolService(
    argumentNamespace: argparse.Namespace,
) -> VerboseElasticIpPoolService:
    runOptionDict = buildRunOptionDict(argumentNamespace)
    providerTimeoutSecondInt = int(runOptionDict["providerTimeoutSecondInt"])
    proxyMaxTimingMillisecondInt = int(
        runOptionDict["proxyMaxTimingMillisecondInt"],
    )

    keyValStoreProxy = KeyValStoreProxy(
        baseUrlStr=str(runOptionDict["keyValBaseUrlStr"]),
        timeoutSecondInt=providerTimeoutSecondInt,
    )
    proxyScrapeProxy = ProxyScrapeProxy(
        baseUrlStr=str(runOptionDict["proxyScrapeBaseUrlStr"]),
        requestValueStr=PROXY_SCRAPE_REQUEST_VALUE_STR,
        proxyTypeStr=str(runOptionDict["proxyTypeStr"]),
        timeoutMillisecondInt=int(runOptionDict["proxyScrapeTimeoutMillisecondInt"]),
        countryFilterStr=str(runOptionDict["countryFilterStr"]),
        sslFilterStr=str(runOptionDict["sslFilterStr"]),
        anonymityFilterStr=str(runOptionDict["anonymityFilterStr"]),
        timeoutSecondInt=providerTimeoutSecondInt,
    )
    geonodeFreeProxyListProxy = GeonodeFreeProxyListProxy(
        timeoutSecondInt=providerTimeoutSecondInt,
    )
    elasticIpHealthCheckProxy = ElasticIpHealthCheckProxy(
        targetUrlStr=str(runOptionDict["targetUrlStr"]),
        timeoutMillisecondInt=proxyMaxTimingMillisecondInt,
    )

    return VerboseElasticIpPoolService(
        keyValStoreProxyStr=str(runOptionDict["keyValStoreProxyStr"]),
        keyValStoreProxy=keyValStoreProxy,
        elasticIpHealthCheckProxy=elasticIpHealthCheckProxy,
        proxyScrapeProxy=proxyScrapeProxy,
        geonodeFreeProxyListProxy=geonodeFreeProxyListProxy,
        loggerLevelStr=runOptionDict["loggerLevelStr"],
        proxyValidationSuccessCountInt=int(
            runOptionDict["proxyValidationSuccessCountInt"],
        ),
        proxyMaxTimingMillisecondInt=proxyMaxTimingMillisecondInt,
        proxySelectionModeStr=str(runOptionDict["proxySelectionModeStr"]),
        proxyResultCountInt=int(runOptionDict["proxyResultCountInt"]),
        proxyCandidateLimitInt=int(runOptionDict["proxyCandidateLimitInt"]),
        proxyShuffleCandidateBool=bool(runOptionDict["proxyShuffleCandidateBool"]),
        proxyRandomSeedInt=runOptionDict["proxyRandomSeedInt"],
        useSavedProxyBool=bool(runOptionDict["useSavedProxyBool"]),
        saveWorkingProxyBool=bool(runOptionDict["saveWorkingProxyBool"]),
        releaseChannelStr=str(runOptionDict["releaseChannelStr"]),
    )


def main(argumentList: list[str] | None = None) -> None:
    argumentParser = buildArgumentParser()
    argumentNamespace = argumentParser.parse_args(argumentList)
    verboseElasticIpPoolService = buildVerboseElasticIpPoolService(argumentNamespace)
    verboseElasticIpPoolService.run()

    print("Final selected proxy:", verboseElasticIpPoolService.finalValueStr)
    print("Ranked proxy list:", verboseElasticIpPoolService.rankedProxyList)


if __name__ == "__main__":
    main()
