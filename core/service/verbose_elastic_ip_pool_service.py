import time

from core.constant.elastic_ip_pool_constant import (
    KEY_VAL_DUMMY_PROXY_KEY_STR,
    KEY_VAL_DUMMY_PROXY_VALUE_STR,
)
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
    ) -> None:
        super().__init__(
            elasticIpHealthCheckProxy=elasticIpHealthCheckProxy,
            keyValStoreProxy=keyValStoreProxy,
            proxyScrapeProxy=proxyScrapeProxy,
            keyValStoreProxyStr=keyValStoreProxyStr,
            dummyProxyValueStr=dummyProxyValueStr,
        )

    def run(self) -> str | None:
        startFloat = time.perf_counter()
        keyValKeyHashStr = self.getKeyValProxyKey()

        print("=== Proxy discovery manual run ===")
        print("KeyVal key source:", self.keyValStoreProxyStr)
        print("KeyVal hashed key:", keyValKeyHashStr)
        print("KeyVal get URL:", self.keyValStoreProxy.buildGetUrl(keyValKeyHashStr))
        print("KeyVal save URL prints only after a working proxy is found")
        print("note: KeyVal is public, so never store credentials or private proxy data")

        print("=== service get flow ===")
        finalValueStr = self.get()

        print("=== final ===")
        print("stored KeyVal key:", keyValKeyHashStr)
        print("stored KeyVal value:", finalValueStr)
        print(
            "open this URL to read it:",
            self.keyValStoreProxy.buildGetUrl(keyValKeyHashStr),
        )
        print("[manual.run] took", self.getElapsedSecondStr(startFloat), "seconds")

        return finalValueStr

    def get(self) -> str | None:
        print("[service.get] start")
        resultStr = super().get()
        print("[service.get] return:", resultStr)
        return resultStr

    def search(self) -> str | None:
        startFloat = time.perf_counter()
        print("[service.search] start ProxyScrape discovery")
        try:
            resultStr = super().search()
            print("[service.search] return:", resultStr)
            return resultStr
        finally:
            print("[service.search] took", self.getElapsedSecondStr(startFloat), "seconds")

    def fetchProxyCandidateText(self) -> str:
        if hasattr(self.proxyScrapeProxy, "buildFetchUrl"):
            print("[proxy_scrape.fetch] URL:", self.proxyScrapeProxy.buildFetchUrl())
        else:
            print("[proxy_scrape.fetch] URL: unavailable from injected proxy")

        proxyCandidateTextStr = super().fetchProxyCandidateText()
        rawProxyList = [
            lineStr.strip()
            for lineStr in proxyCandidateTextStr.splitlines()
            if lineStr.strip()
        ]
        print("[proxy_scrape.fetch] raw proxy count:", len(rawProxyList))
        for indexInt, proxyStr in enumerate(rawProxyList, start=1):
            print(f"[proxy_scrape.fetch] raw proxy {indexInt}:", proxyStr)

        return proxyCandidateTextStr

    def parseProxyCandidateList(self, proxyCandidateTextStr: str) -> list[str]:
        proxyCandidateList = super().parseProxyCandidateList(proxyCandidateTextStr)
        print("[service.parseProxyCandidateList] valid proxy count:", len(proxyCandidateList))
        for indexInt, proxyStr in enumerate(proxyCandidateList, start=1):
            print(f"[service.parseProxyCandidateList] valid proxy {indexInt}:", proxyStr)

        return proxyCandidateList

    def testProxy(self, proxyStr: str) -> dict:
        print("[service.testProxy] testing proxy:", proxyStr)
        resultDict = super().testProxy(proxyStr)
        print(
            "[service.testProxy] result:",
            {
                "proxy": resultDict.get("proxy"),
                "isWorking": resultDict.get("isWorking"),
                "timingMs": resultDict.get("timingMs"),
                "error": resultDict.get("error"),
            },
        )
        return resultDict

    def onProxyValidationPassStart(self, passNumberInt: int) -> None:
        print(
            "[service.validateProxyCandidateList] start",
            self.getProxyValidationPassLabel(passNumberInt),
            "pass",
        )

    def onProxyValidationPassFinish(
        self,
        passNumberInt: int,
        passedProxyCountInt: int,
    ) -> None:
        print(
            "[service.validateProxyCandidateList] finish",
            self.getProxyValidationPassLabel(passNumberInt),
            "pass; passed proxy count:",
            passedProxyCountInt,
        )

    def getProxyValidationPassLabel(self, passNumberInt: int) -> str:
        passLabelByNumberDict = {
            1: "first",
            2: "second",
            3: "third",
        }
        return passLabelByNumberDict.get(passNumberInt, f"pass {passNumberInt}")

    def saveWorkingProxyList(self, workingProxyList: list[dict]) -> str:
        print("[service.saveWorkingProxyList] working proxy count:", len(workingProxyList))
        for indexInt, proxyDict in enumerate(workingProxyList, start=1):
            print(
                f"[service.saveWorkingProxyList] working proxy {indexInt}:",
                proxyDict,
            )

        resultStr = super().saveWorkingProxyList(workingProxyList)
        print("[service.saveWorkingProxyList] stored compact proxy JSON:", resultStr)
        return resultStr

    def check(self) -> str | None:
        print("[service.check] checking KeyVal for existing proxy list")
        keyValKeyStr = self.getKeyValProxyKey()
        print("[service.check] KeyVal key:", keyValKeyStr)
        print(
            "[service.check] KeyVal get URL:",
            self.keyValStoreProxy.buildGetUrl(keyValKeyStr),
        )
        resultStr = super().check()
        print("[service.check] best working saved proxy:", resultStr)
        return resultStr

    def update(self, valueStr: str) -> str:
        print("[service.update] storing proxy list JSON:", valueStr)
        print("[service.update] hashing KeyVal key before save")
        keyValKeyStr = self.getKeyValProxyKey()
        print("[service.update] KeyVal key:", keyValKeyStr)
        print(
            "[service.update] KeyVal save URL:",
            self.keyValStoreProxy.buildSetUrl(
                keyValKeyStr,
                valueStr,
            ),
        )
        resultStr = super().update(valueStr)
        print("[service.update] saved proxy list JSON:", resultStr)
        return resultStr

    def getElapsedSecondStr(self, startFloat: float) -> str:
        return f"{max(0.0, time.perf_counter() - startFloat):.3f}"
