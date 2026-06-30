# 007 - Professional Verbose Logging Cleanup

Update manual proxy-discovery logging so `testKeyValueProxy.py` output is professional, concise, and useful during real runs.

## Goal

Keep the verbose service easy to read while still showing enough information to understand:

- which cache key is used
- whether a saved proxy was reused
- which ProxyScrape URL was requested
- how many candidate rows were returned
- which normalized candidates were tested
- when each validation pass starts and finishes
- how many proxies pass each validation pass
- which proxies are finally selected and saved
- how long discovery and the full manual run took

## Logging Style

Use short operator-friendly prefixes:

- `[run]`
- `[workflow]`
- `[cache]`
- `[discovery]`
- `[proxyscrape]`
- `[candidate]`
- `[validation]`

Avoid noisy implementation labels such as full method names in logs.

## Log Level Control

Add typed constants:

- `LOGGER_LEVEL_ENV_NAME_STR = "LOGGER"`
- `LOGGER_LEVEL_DEBUG_STR = "DEBUG"`
- `LOGGER_LEVEL_INFO_STR = "INFO"`
- `DEFAULT_LOGGER_LEVEL_STR = LOGGER_LEVEL_INFO_STR`

Default logging must be `INFO`.

If environment variable `LOGGER` is set, use that value as the verbose service log level.

- `LOGGER=INFO` prints only the important operator summary.
- `LOGGER=DEBUG` prints detailed candidate and proxy-test lines.
- Invalid or empty values fall back to `INFO`.

## INFO Output

INFO should stay concise and include only high-signal lines:

- hashed storage key
- selected proxy or `none`
- saved proxy cache status
- ProxyScrape row count
- normalized valid proxy count
- validation pass start and finish counts
- final working proxies selected for saving
- compact saved proxy list
- discovery timing
- full run timing

INFO should not print every candidate proxy or every proxy test result.

## DEBUG Output

DEBUG should include everything INFO includes, plus detailed troubleshooting lines:

- KeyVal key source
- cache read URL
- ProxyScrape request URL
- every normalized candidate proxy
- every proxy test attempt
- every proxy test result
- KeyVal save URL

Good examples:

```text
[run] hashed storage key: <hash>
[cache] checking saved proxy list
[cache] usable saved proxy: none
[discovery] starting ProxyScrape search
[proxyscrape] request URL: https://api.proxyscrape.com/?...
[proxyscrape] returned proxy rows: 42
[candidate] valid proxy count: 37
[candidate] 1/37: 203.0.113.10:8080
[validation] first pass started
[validation] testing proxy: 203.0.113.10:8080
[validation] result: proxy=203.0.113.10:8080 isWorking=True timingMs=142 error=None
[validation] first pass finished; passed=18
[cache] working proxies selected: 4
[cache] selected 1/4: proxy=203.0.113.10:8080 averageTimingMs=130 successCount=3
[cache] saving proxy list: ["203.0.113.10:8080"]
[cache] save URL: https://api.keyval.org/set/<hash>/<encoded-value>
[cache] save complete
[discovery] took 6.255 seconds
[run] selected proxy: 203.0.113.10:8080
[run] took 6.255 seconds
```

## Redundancy Rules

- Do not print the same KeyVal key repeatedly.
- Do not print both raw and normalized copies of every proxy unless needed for debugging.
- Print candidate proxies once after parsing and normalization.
- Print KeyVal save URL only when saving actually happens.
- Do not print a fake empty-list save URL when no proxy works.
- Do not print full provider secrets, credentials, private proxy passwords, or session data.

## Architecture Rules

- Keep verbose `print()` output in `core/service/verbose_elastic_ip_pool_service.py`.
- Keep base service logic quiet in `core/service/elastic_ip_pool_service.py`.
- Do not move external API calls into the service layer.
- Keep ProxyScrape and KeyVal request construction in their proxy classes.
- Keep `testKeyValueProxy.py` as a tiny runner that delegates to `VerboseElasticIpPoolService`.

## Tests

Update mocked tests to verify:

1. Default logging level is `INFO`.
2. `LOGGER=DEBUG` enables detailed candidate and proxy-test lines.
3. Invalid `LOGGER` values fall back to `INFO`.
4. No-working-proxy runs print concise cache, candidate count, validation, discovery timing, and run timing lines.
5. Working-proxy runs print pass start and finish lines with pass counts.
6. Working-proxy runs print saved proxy list information only when a save occurs.
7. The old noisy method-name log labels are not required by tests.
8. Tests do not call real ProxyScrape, KeyVal, or external proxy endpoints.
