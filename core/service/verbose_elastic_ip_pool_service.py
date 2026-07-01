import time

from core.constant.elastic_ip_pool_constant import (
    DEFAULT_LOGGER_LEVEL_STR,
    KEY_VAL_DUMMY_PROXY_KEY_STR,
    KEY_VAL_DUMMY_PROXY_VALUE_STR,
    LOGGER_LEVEL_DEBUG_STR,
    LOGGER_LEVEL_ENV_NAME_STR,
    LOGGER_LEVEL_INFO_STR,
)
from core.helper.env_value_helper import getEnvValue
from core.proxy.elastic_ip_health_check_proxy import ElasticIpHealthCheckProxy
from core.proxy.key_val_store_proxy import KeyValStoreProxy
from core.proxy.proxy_scrape_proxy import ProxyScrapeProxy
from core.service.elastic_ip_pool_service import ElasticIpPoolService


class VerboseElasticIpPoolService(ElasticIpPoolService):
    """Printable manual flow service for proxy discovery and KeyVal persistence."""

    def __init__(
        self,
        keyValStoreProxyStr: str = KEY_VAL_DUMMY_PROXY_KEY_STR,
        dummyProxyValueStr: str = KEY_VAL_DUMMY_PROXY_VALUE_STR,
        keyValStoreProxy: KeyValStoreProxy | None = None,
        elasticIpHealthCheckProxy: ElasticIpHealthCheckProxy | None = None,
        proxyScrapeProxy: ProxyScrapeProxy | None = None,
        loggerLevelStr: str | None = None,
    ) -> None:
        self.finalValueStr: str | None = None
        self.rankedProxyList: list[str] | None = None
        super().__init__(
            elasticIpHealthCheckProxy=elasticIpHealthCheckProxy,
            keyValStoreProxy=keyValStoreProxy,
            proxyScrapeProxy=proxyScrapeProxy,
            keyValStoreProxyStr=keyValStoreProxyStr,
            dummyProxyValueStr=dummyProxyValueStr,
        )
        resolvedLoggerLevelStr = loggerLevelStr or getEnvValue(
            LOGGER_LEVEL_ENV_NAME_STR,
            DEFAULT_LOGGER_LEVEL_STR,
        )
        self.loggerLevelStr = self.normalizeLoggerLevel(resolvedLoggerLevelStr)

    def run(self) -> str | None:
        startFloat = time.perf_counter()
        keyValKeyHashStr = self.getKeyValProxyKey()

        self.logInfo("=== Proxy discovery run ===")
        self.logDebug("[run] key source:", self.keyValStoreProxyStr)
        self.logInfo("[run] hashed storage key:", keyValKeyHashStr)
        self.logInfo("[run] log level:", self.loggerLevelStr)
        self.logInfo("[run] note: KeyVal is public; credentials are never stored")

        self.finalValueStr = self.get()

        self.logInfo("[run] selected proxy:", self.finalValueStr or "none")
        self.logDebug("[run] cache read URL:", self.keyValStoreProxy.buildGetUrl(keyValKeyHashStr))
        self.logInfo("[run] took", self.getElapsedSecondStr(startFloat), "seconds")

        return self.finalValueStr

    def get(self) -> str | None:
        self.logDebug("[workflow] resolving usable proxy")
        resultStr = super().get()
        self.logDebug("[workflow] result:", resultStr or "none")
        return resultStr

    def search(self) -> str | None:
        startFloat = time.perf_counter()
        self.logInfo("[discovery] starting ProxyScrape search")
        try:
            resultStr = super().search()
            self.logInfo("[discovery] fastest working proxy:", resultStr or "none")
            return resultStr
        finally:
            self.logInfo("[discovery] took", self.getElapsedSecondStr(startFloat), "seconds")

    def fetchProxyCandidateText(self) -> str:
        if hasattr(self.proxyScrapeProxy, "buildFetchUrl"):
            self.logDebug("[proxyscrape] request URL:", self.proxyScrapeProxy.buildFetchUrl())
        else:
            self.logDebug("[proxyscrape] request URL: unavailable from injected proxy")

        proxyCandidateTextStr = super().fetchProxyCandidateText()
        rawProxyList = [
            lineStr.strip()
            for lineStr in proxyCandidateTextStr.splitlines()
            if lineStr.strip()
        ]
        self.logInfo("[proxyscrape] returned proxy rows:", len(rawProxyList))

        return proxyCandidateTextStr

    def parseProxyCandidateList(self, proxyCandidateTextStr: str) -> list[str]:
        proxyCandidateList = super().parseProxyCandidateList(proxyCandidateTextStr)
        self.logInfo("[candidate] valid proxy count:", len(proxyCandidateList))
        for indexInt, proxyStr in enumerate(proxyCandidateList, start=1):
            self.logDebug(
                f"[candidate] {indexInt}/{len(proxyCandidateList)}:",
                proxyStr,
            )

        return proxyCandidateList

    def testProxy(self, proxyStr: str) -> dict:
        self.logDebug("[validation] testing proxy:", proxyStr)
        resultDict = super().testProxy(proxyStr)
        self.logDebug(
            "[validation] result:",
            f"proxy={resultDict.get('proxy')}",
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
                f"proxy={proxyDict.get('proxy')}",
                f"averageTimingMs={proxyDict.get('averageTimingMs')}",
                f"successCount={proxyDict.get('successCount')}",
            )

        resultStr = super().saveWorkingProxyList(workingProxyList)
        self.logInfo("[cache] stored proxy list:", resultStr)
        return resultStr

    def check(self) -> str | None:
        self.logInfo("[cache] checking saved proxy list")
        resultStr = super().check()
        self.logInfo("[cache] usable saved proxy:", resultStr or "none")
        return resultStr

    def update(self, valueStr: str) -> str:
        keyValKeyStr = self.getKeyValProxyKey()
        self.logInfo("[cache] saving proxy list:", valueStr)
        self.logDebug(
            "[cache] save URL:",
            self.keyValStoreProxy.buildSetUrl(
                keyValKeyStr,
                valueStr,
            ),
        )
        resultStr = super().update(valueStr)
        self.logInfo("[cache] save complete")
        return resultStr

    def getElapsedSecondStr(self, startFloat: float) -> str:
        return f"{max(0.0, time.perf_counter() - startFloat):.3f}"

    def logInfo(self, *valueTuple) -> None:
        if self.loggerLevelStr in {LOGGER_LEVEL_INFO_STR, LOGGER_LEVEL_DEBUG_STR}:
            print(*valueTuple)

    def logDebug(self, *valueTuple) -> None:
        if self.loggerLevelStr == LOGGER_LEVEL_DEBUG_STR:
            print(*valueTuple)

    def normalizeLoggerLevel(self, loggerLevelStr: str) -> str:
        normalizedLoggerLevelStr = str(loggerLevelStr or DEFAULT_LOGGER_LEVEL_STR).upper()
        if normalizedLoggerLevelStr == LOGGER_LEVEL_DEBUG_STR:
            return LOGGER_LEVEL_DEBUG_STR

        return LOGGER_LEVEL_INFO_STR
