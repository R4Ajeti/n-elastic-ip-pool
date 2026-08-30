import json
import time

from n_elastic_ip_pool.constant.elastic_ip_pool_constant import (
    CORE_LOGGER_PREFIX_STR,
    DEFAULT_LOGGER_LEVEL_STR,
    DEFAULT_PROXY_CANDIDATE_LIMIT_INT,
    DEFAULT_PROXY_RELEASE_CHANNEL_STR,
    DEFAULT_PROXY_RESULT_COUNT_INT,
    DEFAULT_PROXY_SAVE_WORKING_PROXY_BOOL,
    DEFAULT_PROXY_SELECTION_MODE_STR,
    DEFAULT_PROXY_SHUFFLE_CANDIDATE_BOOL,
    DEFAULT_PROXY_USE_SAVED_PROXY_BOOL,
    DEBUGGING_ENV_NAME_STR,
    KEY_VAL_DUMMY_PROXY_KEY_STR,
    KEY_VAL_DUMMY_PROXY_VALUE_STR,
    KEY_VAL_STORE_PROXY_ENV_NAME_STR,
    LOGGER_LEVEL_DEBUG_STR,
    LOGGER_LEVEL_ENV_NAME_STR,
    LOGGER_LEVEL_INFO_STR,
    MAX_PROXY_USAGE_COUNT_INT,
    PROXY_MAX_TIMING_MILLISECOND_INT,
    PROXY_VALIDATION_SUCCESS_COUNT_INT,
)
from n_elastic_ip_pool.helper.logger_level_helper import getLoggerLevelNameFromEnv
from n_elastic_ip_pool.helper.sensitive_value_redaction_helper import (
    formatNetworkLocationForLog,
    redactUrlPathValue,
)
from n_elastic_ip_pool.proxy.elastic_ip_health_check_proxy import ElasticIpHealthCheckProxy
from n_elastic_ip_pool.proxy.geonode_free_proxy_list_proxy import GeonodeFreeProxyListProxy
from n_elastic_ip_pool.proxy.key_val_store_proxy import KeyValStoreProxy
from n_elastic_ip_pool.proxy.proxy_scrape_proxy import ProxyScrapeProxy
from n_elastic_ip_pool.repo.firebase_proxy_usage_history_repo import (
    FirebaseProxyUsageHistoryRepo,
)
from n_elastic_ip_pool.service.elastic_ip_pool_service import ElasticIpPoolService


class VerboseElasticIpPoolService(ElasticIpPoolService):
    """Printable manual flow service for proxy discovery and KeyVal persistence."""

    def __init__(
        self,
        keyValStoreProxyStr: str = KEY_VAL_DUMMY_PROXY_KEY_STR,
        dummyProxyValueStr: str = KEY_VAL_DUMMY_PROXY_VALUE_STR,
        keyValStoreProxy: KeyValStoreProxy | None = None,
        elasticIpHealthCheckProxy: ElasticIpHealthCheckProxy | None = None,
        proxyScrapeProxy: ProxyScrapeProxy | None = None,
        geonodeFreeProxyListProxy: GeonodeFreeProxyListProxy | None = None,
        proxyUsageHistoryRepo: FirebaseProxyUsageHistoryRepo | None = None,
        loggerLevelStr: str | None = None,
        proxyValidationSuccessCountInt: int = PROXY_VALIDATION_SUCCESS_COUNT_INT,
        proxyMaxTimingMillisecondInt: int = PROXY_MAX_TIMING_MILLISECOND_INT,
        proxySelectionModeStr: str = DEFAULT_PROXY_SELECTION_MODE_STR,
        proxyResultCountInt: int = DEFAULT_PROXY_RESULT_COUNT_INT,
        proxyCandidateLimitInt: int = DEFAULT_PROXY_CANDIDATE_LIMIT_INT,
        proxyShuffleCandidateBool: bool = DEFAULT_PROXY_SHUFFLE_CANDIDATE_BOOL,
        proxyRandomSeedInt: int | None = None,
        maxProxyUsageCountInt: int = MAX_PROXY_USAGE_COUNT_INT,
        useSavedProxyBool: bool = DEFAULT_PROXY_USE_SAVED_PROXY_BOOL,
        saveWorkingProxyBool: bool = DEFAULT_PROXY_SAVE_WORKING_PROXY_BOOL,
        releaseChannelStr: str = DEFAULT_PROXY_RELEASE_CHANNEL_STR,
        keyValProxyTranslationCountKeyStr: str | None = None,
        proxyTranslationMaxUseCountInt: int | None = None,
        proxyTranslationMinHealthCountInt: int | None = None,
        envFilePathStr: str = ".env",
    ) -> None:
        self.finalValueStr: str | None = None
        self.rankedProxyList: list[str] | None = None
        self.lastCacheHitBool = False
        super().__init__(
            elasticIpHealthCheckProxy=elasticIpHealthCheckProxy,
            keyValStoreProxy=keyValStoreProxy,
            proxyScrapeProxy=proxyScrapeProxy,
            geonodeFreeProxyListProxy=geonodeFreeProxyListProxy,
            proxyUsageHistoryRepo=proxyUsageHistoryRepo,
            keyValStoreProxyStr=keyValStoreProxyStr,
            dummyProxyValueStr=dummyProxyValueStr,
            proxyValidationSuccessCountInt=proxyValidationSuccessCountInt,
            proxyMaxTimingMillisecondInt=proxyMaxTimingMillisecondInt,
            proxySelectionModeStr=proxySelectionModeStr,
            proxyResultCountInt=proxyResultCountInt,
            proxyCandidateLimitInt=proxyCandidateLimitInt,
            proxyShuffleCandidateBool=proxyShuffleCandidateBool,
            proxyRandomSeedInt=proxyRandomSeedInt,
            maxProxyUsageCountInt=maxProxyUsageCountInt,
            useSavedProxyBool=useSavedProxyBool,
            saveWorkingProxyBool=saveWorkingProxyBool,
            releaseChannelStr=releaseChannelStr,
            keyValProxyTranslationCountKeyStr=keyValProxyTranslationCountKeyStr,
            proxyTranslationMaxUseCountInt=proxyTranslationMaxUseCountInt,
            proxyTranslationMinHealthCountInt=proxyTranslationMinHealthCountInt,
            envFilePathStr=envFilePathStr,
        )
        resolvedLoggerLevelStr = loggerLevelStr or getLoggerLevelNameFromEnv(
            LOGGER_LEVEL_ENV_NAME_STR,
            DEBUGGING_ENV_NAME_STR,
            DEFAULT_LOGGER_LEVEL_STR,
        )
        self.loggerLevelStr = self.normalizeLoggerLevel(resolvedLoggerLevelStr)

    def run(self) -> str | None:
        startFloat = time.perf_counter()
        self.lastCacheHitBool = False
        keyValKeyHashStr = self.getKeyValProxyKey()

        self.logInfo("=== Proxy discovery run ===")
        self.logDebug("[run] key source:", "[redacted-key-source]")
        self.logDebug("[run] hashed storage key:", "[redacted-storage-key]")
        self.logInfo("[run] log level:", self.loggerLevelStr)
        self.logDebug(
            "[run] selection:",
            f"mode={self.proxySelectionModeStr}",
            f"resultCount={self.getReadableCountStr(self.proxyResultCountInt)}",
        )
        self.logDebug(
            "[run] validation:",
            f"passes={self.proxyValidationSuccessCountInt}",
            f"maxTimingMs={self.proxyMaxTimingMillisecondInt}",
        )
        self.logDebug(
            "[run] limits:",
            f"translationMaxUseCount={self.proxyTranslationMaxUseCountInt}",
            f"translationMinHealthCount={self.proxyTranslationMinHealthCountInt}",
            f"historicalUsageLimit={self.maxProxyUsageCountInt}",
        )
        self.logDebug(
            "[run] options:",
            f"releaseChannel={self.releaseChannelStr}",
            f"candidateLimit={self.getReadableCountStr(self.proxyCandidateLimitInt)}",
            f"shuffleCandidates={str(self.proxyShuffleCandidateBool).lower()}",
            f"useCache={str(self.useSavedProxyBool).lower()}",
            f"save={str(self.saveWorkingProxyBool).lower()}",
        )
        if self.useSavedProxyBool or self.saveWorkingProxyBool:
            self.logDebug(
                "[run] note: public KeyVal persistence needs a custom key source "
                "for a separate cache namespace",
            )
        else:
            self.logInfo("[run] external cache persistence: disabled")

        self.finalValueStr = self.get()
        if not self.finalValueStr:
            self.logInfo("[translation-count] no selected proxy; no counter to display")

        if not self.lastCacheHitBool:
            self.logInfo(
                "[run] selected proxy:",
                self.redactProxyValue(self.finalValueStr) if self.finalValueStr else "none",
            )
            self.logInfo(
                "[run] working proxy list:",
                self.redactProxyListValue(self.rankedProxyList or []),
            )
        for proxyDict in self.rankedProxyDictList or []:
            self.logDebug(
                "[run] validated proxy:",
                self.redactProxyValue(proxyDict.get("proxy")),
                f"averageTimingMs={proxyDict.get('averageTimingMs')}",
                f"successCount={proxyDict.get('successCount')}",
                f"checkedAt={proxyDict.get('lastCheckedAt')}",
            )
        if self.useSavedProxyBool:
            self.logDebug(
                "[run] cache read URL:",
                self.redactUrlValue(self.keyValStoreProxy.buildGetUrl(keyValKeyHashStr)),
            )
        self.logInfo("[run] took", self.getElapsedSecondStr(startFloat), "seconds")

        return self.finalValueStr

    def get(self) -> str | None:
        self.logDebug("[workflow] resolving usable proxy")
        resultStr = super().get()
        self.logDebug(
            "[workflow] result:",
            self.redactProxyValue(resultStr) if resultStr else "none",
        )
        return resultStr

    def recordSubtitleTranslationResult(
        self,
        proxyStr: str,
        successBool: bool,
        proxyFailureBool: bool = False,
        rediscoverBool: bool = True,
    ) -> str | None:
        self.finalValueStr = super().recordSubtitleTranslationResult(
            proxyStr, successBool, proxyFailureBool, rediscoverBool,
        )
        return self.finalValueStr

    def onProxyTranslationCountFailure(self, error: Exception) -> None:
        self.logDebug("[translation-count] using local state:", error.__class__.__name__)

    def onProxyTranslationCountUpdated(
        self,
        keyStr: str,
        countInt: int,
        storedBool: bool,
    ) -> None:
        self.logProxyTranslationCountState(
            {"key": keyStr, "count": countInt, "source": "keyval" if storedBool else "local"},
            "write",
            storedBool,
        )

    def logSelectedProxyTranslationCount(self, proxyStr: str) -> None:
        if self.loggerLevelStr not in {LOGGER_LEVEL_INFO_STR, LOGGER_LEVEL_DEBUG_STR}:
            return
        self.logProxyTranslationCountState(
            self.getProxyTranslationCountState(proxyStr), "read", proxyStr=proxyStr,
        )

    def logProxyTranslationCountState(
        self,
        stateDict: dict,
        eventStr: str,
        storedBool: bool | None = None,
        proxyStr: str | None = None,
    ) -> None:
        fieldList = [
            f"key={stateDict['key']}",
            f"count={stateDict['count']}",
            f"source={stateDict['source']}",
            f"event={eventStr}",
        ]
        if storedBool is not None:
            fieldList.append(f"stored={str(storedBool).lower()}")
        if proxyStr is not None:
            fieldList.append(f"proxy={self.redactProxyValue(proxyStr)}")
        self.logInfo(
            "[translation-count]",
            *fieldList,
        )

    def search(self) -> str | None:
        startFloat = time.perf_counter()
        self.logInfo("[discovery] starting ProxyScrape search")
        try:
            resultStr = super().search()
            self.logDebug(
                "[discovery] fastest working proxy:",
                self.redactProxyValue(resultStr) if resultStr else "none",
            )
            if resultStr:
                self.logSelectedProxyTranslationCount(resultStr)
            return resultStr
        finally:
            self.logInfo("[discovery] took", self.getElapsedSecondStr(startFloat), "seconds")

    def fetchProxyCandidateText(self) -> str:
        return self.fetchProxyScrapeCandidateText()

    def fetchProxyScrapeCandidateText(self) -> str:
        if hasattr(self.proxyScrapeProxy, "buildFetchUrl"):
            self.logDebug("[proxyscrape] request URL:", self.proxyScrapeProxy.buildFetchUrl())
        else:
            self.logDebug("[proxyscrape] request URL: unavailable from injected proxy")

        proxyCandidateTextStr = super().fetchProxyScrapeCandidateText()
        rawProxyList = [
            lineStr.strip()
            for lineStr in proxyCandidateTextStr.splitlines()
            if lineStr.strip()
        ]
        self.logInfo("[proxyscrape] returned proxy rows:", len(rawProxyList))

        return proxyCandidateTextStr

    def fetchGeonodeFreeProxyCandidateText(self) -> str:
        if hasattr(self.geonodeFreeProxyListProxy, "buildFetchUrl"):
            self.logDebug(
                "[geonode] request URL:",
                self.geonodeFreeProxyListProxy.buildFetchUrl(),
            )
        else:
            self.logDebug("[geonode] request URL: unavailable from injected proxy")

        proxyCandidateTextStr = super().fetchGeonodeFreeProxyCandidateText()
        rawProxyList = [
            lineStr.strip()
            for lineStr in proxyCandidateTextStr.splitlines()
            if lineStr.strip()
        ]
        self.logInfo("[geonode] returned proxy rows:", len(rawProxyList))

        return proxyCandidateTextStr

    def parseProxyCandidateList(self, proxyCandidateTextStr: str) -> list[str]:
        proxyCandidateList = super().parseProxyCandidateList(proxyCandidateTextStr)
        self.logInfo("[candidate] valid proxy count:", len(proxyCandidateList))
        for indexInt, proxyStr in enumerate(proxyCandidateList, start=1):
            self.logDebug(
                f"[candidate] {indexInt}/{len(proxyCandidateList)}:",
                self.redactProxyValue(proxyStr),
            )

        return proxyCandidateList

    def testProxy(self, proxyStr: str) -> dict:
        self.logDebug("[validation] testing proxy:", self.redactProxyValue(proxyStr))
        resultDict = super().testProxy(proxyStr)
        self.logDebug(
            "[validation] result:",
            f"proxy={self.redactProxyValue(resultDict.get('proxy'))}",
            f"isWorking={resultDict.get('isWorking')}",
            f"timingMs={resultDict.get('timingMs')}",
            f"error={resultDict.get('error')}",
        )
        return resultDict

    def onProxyValidationPassStart(self, passNumberInt: int) -> None:
        self.logInfo(
            "[validation]",
            self.getProxyValidationPassLabel(passNumberInt),
            "pass started",
        )

    def onProxyValidationPassFinish(
        self,
        passNumberInt: int,
        passedProxyCountInt: int,
    ) -> None:
        self.logInfo(
            "[validation]",
            self.getProxyValidationPassLabel(passNumberInt),
            f"pass finished; passed={passedProxyCountInt}",
        )

    def getProxyValidationPassLabel(self, passNumberInt: int) -> str:
        passLabelByNumberDict = {
            1: "first",
            2: "second",
            3: "third",
        }
        return passLabelByNumberDict.get(passNumberInt, f"pass {passNumberInt}")

    def saveWorkingProxyList(self, workingProxyList: list[dict]) -> str:
        self.logInfo("[cache] working proxies selected:", len(workingProxyList))
        for indexInt, proxyDict in enumerate(workingProxyList, start=1):
            self.logInfo(
                f"[cache] selected {indexInt}/{len(workingProxyList)}:",
                f"proxy={self.redactProxyValue(proxyDict.get('proxy'))}",
                f"averageTimingMs={proxyDict.get('averageTimingMs')}",
                f"successCount={proxyDict.get('successCount')}",
            )

        resultStr = super().saveWorkingProxyList(workingProxyList)
        if resultStr:
            self.logInfo("[cache] stored proxy list:", self.redactProxyListValue(resultStr))
        else:
            self.logInfo("[cache] stored proxy list: skipped")

        return resultStr

    def onWorkingProxySaveFailure(self, error: Exception) -> None:
        self.logInfo("[cache] save skipped:", str(error))

    def onWorkingProxySaveSkipped(self) -> None:
        if self.saveWorkingProxyBool and not self.hasWorkingProxySaveTarget():
            self.logInfo(
                "[cache] save skipped: KeyVal key source or proxy required",
            )
            return None

        self.logInfo("[cache] save skipped: disabled")
        return None

    def onProxyUsageHistoryFailure(self, error: Exception) -> None:
        self.logDebug("[usage-history] skipped:", error.__class__.__name__)

    def onSavedProxyValueRead(self, keyStr: str, resultDict: dict | None) -> None:
        if resultDict is None:
            self.logInfo("[proxy-cache]", f"key={keyStr}", "value=unavailable source=unavailable event=read")
            return
        self.logProxyCacheValue(
            keyStr,
            str(resultDict.get("value") or ""),
            "keyval" if resultDict.get("exists") else "missing",
            "read",
        )

    def logProxyCacheValue(
        self, keyStr: str, valueStr: str, sourceStr: str, eventStr: str,
    ) -> None:
        try:
            proxyList = self.parseSavedProxyList(valueStr)
        except (TypeError, ValueError):
            proxyList = []
        safeValueStr = self.redactProxyListValue([
            proxyDict["proxy"] for proxyDict in proxyList
        ]) if proxyList or not valueStr else "[redacted]"
        self.logInfo(
            "[proxy-cache]",
            f"variable={KEY_VAL_STORE_PROXY_ENV_NAME_STR}",
            f"key={keyStr}",
            f"value={safeValueStr}",
            f"source={sourceStr}",
            f"event={eventStr}",
            "state=stored-value",
        )

    def check(self) -> str | None:
        self.logInfo("[cache] checking saved proxy list")
        resultStr = super().check()
        self.lastCacheHitBool = bool(resultStr)
        logFunction = self.logInfo if resultStr else self.logDebug
        logFunction(
            "[cache] usable saved proxy:",
            self.redactProxyValue(resultStr) if resultStr else "none",
        )
        logFunction(
            "[cache] working proxy list:",
            self.redactProxyListValue(self.rankedProxyList or []),
        )
        if resultStr:
            self.logSelectedProxyTranslationCount(resultStr)
        return resultStr

    def update(self, valueStr: str) -> str:
        keyValKeyStr = self.getKeyValProxyKey()
        self.logInfo("[cache] saving proxy list:", self.redactProxyListValue(valueStr))
        self.logDebug(
            "[cache] save URL:",
            self.redactUrlValue(self.keyValStoreProxy.buildSetUrl(keyValKeyStr, valueStr)),
        )
        resultStr = super().update(valueStr)
        self.logProxyCacheValue(keyValKeyStr, resultStr, "keyval", "write")
        self.logInfo("[cache] save complete")
        return resultStr

    def getElapsedSecondStr(self, startFloat: float) -> str:
        return f"{max(0.0, time.perf_counter() - startFloat):.3f}"

    def getReadableCountStr(self, countInt: int) -> str:
        if countInt:
            return str(countInt)

        return "all"

    def logInfo(self, *valueTuple) -> None:
        if self.loggerLevelStr in {LOGGER_LEVEL_INFO_STR, LOGGER_LEVEL_DEBUG_STR}:
            self.logMessage(LOGGER_LEVEL_INFO_STR, *valueTuple)

    def logDebug(self, *valueTuple) -> None:
        if self.loggerLevelStr == LOGGER_LEVEL_DEBUG_STR:
            self.logMessage(LOGGER_LEVEL_DEBUG_STR, *valueTuple)

    def logMessage(self, levelStr: str, *valueTuple) -> None:
        messageStr = " ".join(str(value) for value in valueTuple)
        for lineStr in messageStr.splitlines() or [""]:
            print(CORE_LOGGER_PREFIX_STR, f"[{levelStr}]", lineStr)

    def normalizeLoggerLevel(self, loggerLevelStr: str) -> str:
        normalizedLoggerLevelStr = str(loggerLevelStr or DEFAULT_LOGGER_LEVEL_STR).upper()
        levelAliasDict = {
            "WARN": "WARNING", "WARM": "WARNING", "0": "NOTSET",
            "10": "DEBUG", "20": "INFO", "30": "WARNING",
            "40": "ERROR", "50": "CRITICAL",
        }
        normalizedLoggerLevelStr = levelAliasDict.get(
            normalizedLoggerLevelStr.strip(), normalizedLoggerLevelStr.strip(),
        )
        if normalizedLoggerLevelStr == "NOTSET":
            return LOGGER_LEVEL_DEBUG_STR
        if normalizedLoggerLevelStr in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            return normalizedLoggerLevelStr

        return LOGGER_LEVEL_INFO_STR

    def redactProxyValue(self, proxyValue) -> str:
        return formatNetworkLocationForLog(proxyValue)

    def redactProxyListValue(self, proxyListValue) -> str:
        if isinstance(proxyListValue, str):
            try:
                proxyListValue = json.loads(proxyListValue)
            except (TypeError, ValueError):
                return "[redacted]"
        if not isinstance(proxyListValue, list):
            return "[redacted]"
        return json.dumps([self.redactProxyValue(value) for value in proxyListValue])

    def redactUrlValue(self, urlValue) -> str:
        return redactUrlPathValue(urlValue)
