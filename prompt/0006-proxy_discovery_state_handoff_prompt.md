# 008 - Proxy Discovery State Handoff

Use this prompt as the current-state handoff after `prompt/0005_professional_verbose_logging_prompt.md`.

The project has moved past the initial skeleton and now includes real ProxyScrape discovery, KeyVal proxy-list persistence, three-pass proxy validation, saved proxy reuse, and professional INFO/DEBUG verbose logging.

## Current State

The implementation currently follows the N-layer flow:

```text
Entry point -> Service -> Repo -> Storage
Entry point -> Service -> Proxy -> External API
```

The important active files are:

```text
core/constant/elastic_ip_pool_constant.py
core/helper/env_value_helper.py
core/helper/proxy_address_format_helper.py
core/helper/string_hash_helper.py
core/proxy/elastic_ip_health_check_proxy.py
core/proxy/key_val_store_proxy.py
core/proxy/proxy_scrape_proxy.py
core/repo/elastic_ip_pool_repo.py
core/service/elastic_ip_pool_service.py
core/service/verbose_elastic_ip_pool_service.py
testKeyValueProxy.py
```

## Completed Behavior

### KeyVal persistence

- The configured KeyVal source string is hashed before KeyVal reads and writes.
- KeyVal external calls stay inside `core/proxy/key_val_store_proxy.py`.
- `KeyValStoreProxy.buildSetUrl()` URL-encodes the compact JSON proxy list.
- The service saves a compact JSON list of proxy strings, not full ranking metadata.
- The service does not save `[]` when no working proxies exist.
- KeyVal provider failure statuses such as `-KEY-OR-VALUE-TOO-LONG-` are treated as unsuccessful saves.
- Search can still return a working proxy even when the KeyVal save fails.

### ProxyScrape discovery

- ProxyScrape external calls stay inside `core/proxy/proxy_scrape_proxy.py`.
- The ProxyScrape URL is built from typed constants and constructor defaults.
- The service fetches newline-delimited candidate proxy text through the proxy layer only.
- Candidate parsing normalizes proxy values and removes duplicates.
- Malformed rows are ignored before validation.

### Health checking

- Proxy health checks stay inside `core/proxy/elastic_ip_health_check_proxy.py`.
- Proxy values are normalized to reusable `host:port` form before network use.
- Proxy values with embedded usernames, passwords, tokens, unsupported schemes, invalid ports, or invalid host formats are rejected.
- The health-check timeout uses `PROXY_MAX_TIMING_MILLISECOND_INT`, converted to seconds.
- Results are normalized with `proxy`, `isWorking`, `timingMs`, `checkedAt`, `error`, and `statusCode`.

### Service selection rules

- `ElasticIpPoolService.get()` first checks saved KeyVal proxies.
- Saved proxies are re-tested before reuse.
- If no saved proxy is usable, the service searches ProxyScrape.
- Candidate proxies must pass `PROXY_VALIDATION_SUCCESS_COUNT_INT` validation passes.
- Proxies slower than `PROXY_MAX_TIMING_MILLISECOND_INT` are rejected.
- Working proxies are ranked by average timing ascending, then proxy string.
- The fastest working proxy is returned.
- If no proxy works, the service returns `None` and does not save to KeyVal.

### Verbose logging

- Manual-run print output lives in `core/service/verbose_elastic_ip_pool_service.py`.
- Base service logic stays quiet in `core/service/elastic_ip_pool_service.py`.
- Logging uses operator-friendly prefixes such as `[run]`, `[cache]`, `[discovery]`, `[proxyscrape]`, `[candidate]`, and `[validation]`.
- Default log level is `INFO`.
- `LOGGER=DEBUG` enables detailed candidate and proxy-test lines.
- Invalid or empty `LOGGER` values fall back to `INFO`.
- INFO logs include high-signal cache status, candidate counts, validation pass counts, selected proxy, saved proxy list status, discovery timing, and run timing.
- DEBUG logs include KeyVal key source, request URLs, every normalized candidate, and every proxy test result.

## Raw Proxy Examples

The current proxy implementations have matching raw example contracts:

```text
raw/proxy/elastic_ip_health_check_proxy/request.txt
raw/proxy/elastic_ip_health_check_proxy/json/input.json
raw/proxy/elastic_ip_health_check_proxy/json/output.json
raw/proxy/key_val_store_proxy/request.txt
raw/proxy/key_val_store_proxy/json/input.json
raw/proxy/key_val_store_proxy/json/output.json
raw/proxy/proxy_scrape_proxy/request.txt
raw/proxy/proxy_scrape_proxy/json/input.json
raw/proxy/proxy_scrape_proxy/json/output.json
```

If any proxy request or response shape changes, update the matching raw files in the same change.

## Test Coverage

The current tests are mocked and should not call real ProxyScrape, KeyVal, or proxy endpoints.

Covered areas include:

- KeyVal get/set URL construction, response parsing, URL encoding, and provider failure statuses.
- ProxyScrape URL construction and normalized fetch response shape.
- Elastic proxy health checking, timeout behavior, invalid proxy rejection, and normalized result shape.
- Proxy candidate parsing, duplicate removal, malformed row rejection, and empty/failing ProxyScrape responses.
- Saved KeyVal proxy reuse after validation.
- Fallback to ProxyScrape when saved data is missing, invalid, corrupted, or failing.
- Three-pass validation behavior.
- Slow proxy rejection.
- Fastest-proxy ranking.
- Compact saved proxy-list construction within `KEY_VAL_MAX_VALUE_LENGTH_INT`.
- Verbose INFO/DEBUG logging behavior and `LOGGER` env fallback.

Run:

```bash
python3 -m unittest discover -s test -p "test_*.py"
```

Optional manual runner:

```bash
LOGGER=INFO python3 testKeyValueProxy.py
LOGGER=DEBUG python3 testKeyValueProxy.py
```

The manual runner may call live configured services. Unit tests must remain isolated from live network dependencies.

## Known Follow-Up Checks

Before continuing feature work, verify `testKeyValueProxy.py` passes the resolved `keyValStoreProxyStr` into `VerboseElasticIpPoolService`. It currently resolves the environment value and should keep the runner thin, but the service construction must actually use the resolved value.

Also keep these guardrails:

- Do not move external API calls into services.
- Do not store business rules in proxies.
- Do not put provider-specific logic in helpers.
- Do not add real proxy credentials, API keys, tokens, private IPs, session cookies, or production request dumps.
- Do not implement ban bypass, scraping evasion, CAPTCHA bypass, account abuse, rate-limit bypass, stealth behavior, or credential abuse.
- Keep new tests mocked unless a manual integration runner is explicitly being used.

## Next Prompt Starting Point

Continue from the current implementation instead of rebuilding the skeleton.

Good next work items would be:

1. Fix or confirm the manual runner uses the resolved KeyVal source string.
2. Add a focused test for the manual runner staying thin and passing configuration correctly.
3. Review service/proxy/helper boundaries with `skill/service-boundary-review/SKILL.md`.
4. Only after the runner and service contracts are stable, decide whether the next milestone should improve in-memory repo behavior or persistent storage.
