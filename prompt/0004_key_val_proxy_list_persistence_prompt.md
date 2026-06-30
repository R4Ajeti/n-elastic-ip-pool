# 006 - KeyVal Proxy List Persistence and Manual Logging

Update the proxy discovery persistence flow so `testKeyValueProxy.py` returns a real validated proxy when one exists, saves only working proxies to KeyVal, and saves nothing when no proxy works.

## Problem

The old manual runner saved this dummy value to KeyVal:

```json
{
  "status": "SUCCESS",
  "key": "a9362079373ac299322a9a8db4d94b5b65c392e1a188d30f5f899fb17ccb4a65",
  "val": "123.4.5.6:6666"
}
```

That is wrong for the real ProxyScrape discovery flow. The key may be hashed, but the saved value must be a reusable proxy list, not a hash and not the old dummy proxy.

## Required Behavior

1. Keep hashing the configured KeyVal key before reading or writing.
2. Fetch candidates from ProxyScrape through the proxy layer only.
3. Validate candidate proxies in three pass waves:
   - Print when the first pass starts.
   - Print when the first pass finishes and how many proxies passed it.
   - Print when the second pass starts.
   - Print when the second pass finishes and how many proxies passed it.
   - Print when the third pass starts.
   - Print when the third pass finishes and how many proxies passed it.
4. Reject any proxy test result slower than `PROXY_MAX_TIMING_MILLISECOND_INT`.
   - Add/use a typed constant such as `PROXY_MAX_TIMING_MILLISECOND_INT`.
   - The current active value may be lowered, for example `2000`.
   - A proxy slower than this value must not be returned or saved.
   - The health-check proxy network timeout must also use this limit, converted to seconds, so one dead proxy does not block the whole pass for the older 10-second default.
5. When working proxies are found:
   - Sort by average timing ascending.
   - Return the fastest proxy from `get()`.
   - Save a compact JSON list of proxy strings to KeyVal, fastest first.
   - Example saved value: `["proxy-one.example.net:8080"]`
   - Do not save full metadata objects because KeyVal's path-style API can return `-KEY-OR-VALUE-TOO-LONG-`.
6. When no working proxies are found:
   - Return `None`.
   - Do not save anything to KeyVal.
   - Do not save `[]`.
7. KeyVal save URLs must URL-encode the JSON value through `KeyValStoreProxy.buildSetUrl()`.
   - Example non-empty string-list path value starts with `%5B%22`.
8. Remove any manual-run path that force-saves `KEY_VAL_DUMMY_PROXY_VALUE_STR`.
9. Do not save `123.4.5.6:6666` unless a test explicitly passes it as custom sample data.

## Architecture Rules

- KeyVal request construction and URL encoding stay inside `core/proxy/key_val_store_proxy.py`.
- ProxyScrape fetching stays inside `core/proxy/proxy_scrape_proxy.py`.
- Proxy health testing stays inside `core/proxy/elastic_ip_health_check_proxy.py`.
- Proxy selection, timing threshold, validation count, ranking, and persistence decisions stay inside `core/service/elastic_ip_pool_service.py`.
- Verbose printing belongs in `core/service/verbose_elastic_ip_pool_service.py`.
- Tests must not call real ProxyScrape, KeyVal, or external proxy endpoints.

## Manual Runner

Keep `testKeyValueProxy.py` as a tiny generic manual runner only:

- Resolve `KEY_VAL_STORE_PROXY_ENV_NAME_STR` with `getEnvValue()`.
- Instantiate `VerboseElasticIpPoolService`.
- Call `.run()`.
- Do not put fake proxy classes or long smoke-test scenarios in this file.
- Put mocked no-working-proxy, working-proxy, slow-proxy, and logging coverage in unit tests under `test/`.

The verbose service should print:

- ProxyScrape request URL.
- Every raw proxy returned by the ProxyScrape response.
- Every normalized valid proxy candidate.
- Start and finish of first, second, and third pass.
- Count of proxies that passed each pass.
- Every proxy test attempt and result.
- Each final working proxy record.
- The compact JSON value saved to KeyVal, only when at least one proxy works.
- The URL-encoded KeyVal save URL, only when saving.
- Total elapsed seconds for ProxyScrape discovery/search in this format: `took 6.255 seconds`.
- Total elapsed seconds for the full manual run in this format: `took 6.255 seconds`.

## Tests

Cover at least:

1. `testKeyValueProxy.py` stays small and delegates to `VerboseElasticIpPoolService`.
2. No working proxies returns `None` and does not call KeyVal `setValue()`.
3. Working proxies returns the fastest proxy and saves a compact JSON string list.
4. Slow proxies over `PROXY_MAX_TIMING_MILLISECOND_INT` are rejected.
5. First, second, and third pass start logs are printed.
6. First, second, and third pass finish logs are printed with pass counts.
7. Discovery/search elapsed time and full manual run elapsed time are printed.
8. KeyVal provider failure status such as `-KEY-OR-VALUE-TOO-LONG-` is treated as not stored.
9. Unit tests use mocks/fakes only and do not make real network calls.

Run:

```bash
python3 -m unittest discover -s test -p "test_*.py"
python3 testKeyValueProxy.py
```

The unit test command must not make real network calls. The manual runner may call real configured services because it is explicitly a manual integration runner.
