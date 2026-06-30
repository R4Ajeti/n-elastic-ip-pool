# KeyVal Dummy Proxy Verbose Service Prompt

## Objective

Move the manual KeyVal dummy proxy runner logic out of `testKeyValueProxy.py` and into a descriptively named service while keeping the N-layer architecture intact.

## Entry Point

`testKeyValueProxy.py` must stay as a thin entry point only. It should read configuration, construct the service, and call `run()`.

Read `keyValStoreProxyStr` from the process environment or `.env` using the same env variable name. If it is not set, fall back to `KEY_VAL_DUMMY_PROXY_KEY_STR`.

The entry point should create the service like this:

```python
service = VerboseElasticIpPoolService(
    keyValStoreProxyStr=keyValStoreProxyStr,
    dummyProxyValueStr=SAFE_HARDCODED_DUMMY_PROXY_STR,
)
service.run()
```

## Flow

- `keyValStoreProxyStr` is the source string for the KeyVal key.
- The service hashes `keyValStoreProxyStr` before calling KeyVal.
- The service stores the safe dummy proxy value as the KeyVal value.
- The entry point must not construct KeyVal URLs or call the KeyVal proxy directly.
- External API calls must stay inside `core/proxy/`.

## Acceptance Criteria

- `testKeyValueProxy.py` contains only entry-point orchestration.
- Verbose print logic lives in `core/service/verbose_elastic_ip_pool_service.py`.
- The KeyVal key is derived from `hashStringValue(keyValStoreProxyStr)`.
- The KeyVal value is `SAFE_HARDCODED_DUMMY_PROXY_STR`.
- `keyValStoreProxyStr` is read from env or `.env`, then defaults to `KEY_VAL_DUMMY_PROXY_KEY_STR`.
- Unit tests cover env fallback and the verbose service flow without calling the live KeyVal API.
- The live runner still works with `. ./activate && python testKeyValueProxy.py`.
