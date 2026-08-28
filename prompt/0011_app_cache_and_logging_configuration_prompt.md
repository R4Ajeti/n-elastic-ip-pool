# 011 - App Entry Point, Default Cache Persistence, and Environment Logging

Follow `AGENTS.md` and the relevant repository skill before making changes:

- `skill/service-boundary-review/SKILL.md`

Use `skill/proxy-example-contract/SKILL.md` only if a proxy implementation is
modified. The work described here does not require proxy changes or raw proxy
example updates.

## Goal

Keep the root application entry point, KeyVal cache defaults, and verbose
logging environment behavior aligned as one supported runtime flow.

The intended command is:

```bash
python3 app/key_value_proxy_app.py
```

The application should:

1. Read the KeyVal cache before discovery.
2. Revalidate cached proxies before returning one.
3. Discover and validate new proxies when the cache has no usable value.
4. Save the resulting working proxy list to KeyVal by default.
5. Resolve verbose output from `DEBUGGING` and `LOGGER` using the same
   precedence contract as `n-user-agent`.

## App Entry Point

Use:

```text
app/key_value_proxy_app.py
```

The app entry point replaces the old root `testKeyValueProxy.py`-style manual
flow and the removed `script/key_value_proxy_runner.py` entry point.

It must:

- Read `keyValStoreProxyStr` from the process environment or `.env`.
- Fall back to `KEY_VAL_DUMMY_PROXY_KEY_STR` when no value is configured.
- Pass the resolved key source into `VerboseElasticIpPoolService`.
- Call `run()` on the service.
- Print the final selected proxy and ranked proxy list.
- Keep provider calls and business rules out of the app layer.

Required flow:

```text
App Entry Point -> Service -> Proxy -> External API
```

## Default Cache Behavior

The default service configuration must enable both cache reads and cache
writes:

```python
DEFAULT_PROXY_USE_SAVED_PROXY_BOOL = True
DEFAULT_PROXY_SAVE_WORKING_PROXY_BOOL = True
```

The built-in non-empty KeyVal source is a valid save target. An injected
`KeyValStoreProxy` is also a valid save target. Reject saving only when there is
neither a non-empty key source nor an injected KeyVal proxy.

Keep explicit opt-out behavior:

```python
ElasticIpPoolService(saveWorkingProxyBool=False)
```

Cache behavior must remain:

```text
get()
  -> check KeyVal when useSavedProxyBool is true
  -> parse the saved proxy list
  -> skip usage-disabled proxies
  -> health-check every saved candidate before reuse
  -> return a usable saved proxy when available
  -> otherwise discover, validate, rank, and save working proxies
```

Do not treat KeyVal as a trusted local cache. It is an external public storage
provider by default, and cached proxy values can become unavailable between
runs.

## Logging Environment Contract

Support these environment variables:

```text
DEBUGGING=true
LOGGER=info
```

Add the typed constant:

```python
DEBUGGING_ENV_NAME_STR = "DEBUGGING"
```

Resolve logging with this precedence:

1. A nonblank `DEBUGGING` value takes precedence over `LOGGER`.
2. `DEBUGGING=true` selects `DEBUG`.
3. Any other nonblank `DEBUGGING` value selects `INFO`, including `false`.
4. Blank `DEBUGGING` falls back to `LOGGER`.
5. If process variables are absent, read the same names from `.env`.
6. Normalize `LOGGER` case, so `LOGGER=info` becomes `INFO`.
7. If no valid supported level is resolved, fall back to `INFO`.
8. An explicit `loggerLevelStr` constructor argument continues to override
   environment resolution.

For the example configuration:

```text
DEBUGGING=true
LOGGER=info
```

the effective verbose service level must be:

```text
DEBUG
```

Implement generic environment resolution in:

```text
core/helper/logger_level_helper.py
```

The verbose service should consume the helper result. Do not move logging
configuration into a proxy or repo.

## Logging Output and Safety

Keep the existing output split:

- `INFO` prints the compact operator flow and summary.
- `DEBUG` adds workflow details, provider request shapes, candidates, and
  validation results.

Continue redacting:

- proxy network locations
- KeyVal key paths
- KeyVal values in URLs
- storage key hashes
- credentials or provider secrets

Do not log real `.env` values, tokens, proxy passwords, Firebase credentials,
or private infrastructure details.

## Documentation

Update `README.md` so it documents:

- `app/key_value_proxy_app.py` as the supported manual entry point.
- `DEBUGGING=true` and `DEBUGGING=false` behavior.
- `DEBUGGING` precedence over `LOGGER`.
- lowercase `LOGGER=info` normalization.
- cache reads and writes being enabled by default.
- `saveWorkingProxyBool=False` as the read-only service option.
- the public KeyVal namespace warning.

Remove or update examples that still present the removed
`script/key_value_proxy_runner.py` as the supported entry point.

## Tests

Use mocked, offline unit tests only. Do not call live proxy providers, KeyVal,
Firebase, or health-check endpoints.

Cover at least:

1. Cache reads are enabled by default.
2. Working proxy-list saves are enabled by default.
3. An explicit `saveWorkingProxyBool=False` disables saves.
4. The default non-empty KeyVal key source is a valid save target.
5. An empty key source without an injected KeyVal proxy is rejected.
6. `DEBUGGING=true` overrides `LOGGER=info` and resolves to `DEBUG`.
7. `DEBUGGING=false` overrides `LOGGER=debug` and resolves to `INFO`.
8. Missing `DEBUGGING` falls back to `LOGGER`.
9. Blank process-level `DEBUGGING` falls back to process-level `LOGGER` even
   when `.env` contains a nonblank `DEBUGGING` value.
10. `.env` values use the same precedence behavior.
11. Invalid explicit verbose levels fall back to `INFO`.
12. Debug output continues to redact proxy values.

Suggested test files:

```text
test/constant/test_elastic_ip_pool_constant.py
test/helper/test_logger_level_helper.py
test/service/test_elastic_ip_pool_service.py
test/service/test_verbose_elastic_ip_pool_service.py
```

## Known Cleanup Requirement

The removed runner may still have a stale test:

```text
test/test_key_value_proxy_runner.py
```

If it still imports `script.key_value_proxy_runner`, migrate its relevant app
entry-point coverage or remove the obsolete test. The full discovery suite is
not clean until no test imports the removed `script/` package.

## Validation

Run the layer tests without live internet access:

```bash
python3 -m unittest discover -s test/constant -p "test_*.py"
python3 -m unittest discover -s test/helper -p "test_*.py"
python3 -m unittest discover -s test/proxy -p "test_*.py"
python3 -m unittest discover -s test/repo -p "test_*.py"
python3 -m unittest discover -s test/service -p "test_*.py"
```

After resolving the stale runner test, also run:

```bash
python3 -m unittest discover -s test -p "test_*.py"
```

Before finishing, verify:

- N-layer boundaries still pass review.
- Constants remain constants only and use typed suffixes.
- The logger-level helper remains generic and reusable.
- The service owns cache and logging-level decisions.
- No proxy request or response contract changed.
- No raw proxy examples require updates.
- No secrets or `.env` files are committed.
- Documentation matches the supported app entry point.
