# 012 - Proxy Pool Environment Configuration

Follow `AGENTS.md` and the relevant repository skills before making changes:

- `skill/service-boundary-review/SKILL.md`
- `skill/proxy-example-contract/SKILL.md` when modifying `KeyValStoreProxy`

## Goal

Support environment-based configuration for optional KeyVal persistence and
proxy health-check behavior through the application entry point.

The supported runtime entry point is:

```bash
python3 app/key_value_proxy_app.py
```

## Environment Variables

Support these variables from the process environment or `.env`:

```text
KEY_VAL_BASE_URL=
KEY_VAL_AUTH_TOKEN=
PROXY_TEST_TARGET_URL=
PROXY_MAX_TIMING_MILLISECOND=
```

Use these descriptions in `env_example`, with comments kept inline:

```text
KEY_VAL_BASE_URL= # Optional KeyVal-compatible base URL; leave blank to keep persistence local.
KEY_VAL_AUTH_TOKEN= # Optional bearer token for a private KeyVal-compatible provider.
PROXY_TEST_TARGET_URL= # URL every candidate proxy must reach to be considered working.
PROXY_MAX_TIMING_MILLISECOND= # Maximum accepted proxy response time in milliseconds; defaults to 2000.
```

Keep the existing `keyValStoreProxyStr` environment variable as the KeyVal
namespace/key source for backward compatibility. The service hashes this value
before using it as a storage key.

## KeyVal Configuration

Add typed constants for the environment names:

```python
KEY_VAL_BASE_URL_ENV_NAME_STR = "KEY_VAL_BASE_URL"
KEY_VAL_AUTH_TOKEN_ENV_NAME_STR = "KEY_VAL_AUTH_TOKEN"
```

Application behavior must be:

1. When `KEY_VAL_BASE_URL` is blank or missing, disable external KeyVal cache
   reads and writes for the app run.
2. When `KEY_VAL_BASE_URL` is nonblank, construct `KeyValStoreProxy` with that
   base URL and enable cache reads and writes.
3. When `KEY_VAL_AUTH_TOKEN` is nonblank, send it as:

   ```text
   Authorization: Bearer <token>
   ```

4. When `KEY_VAL_AUTH_TOKEN` is blank, omit the `Authorization` header.
5. Never log the bearer token or place it in request URLs.
6. Keep HTTP request construction and authentication inside the proxy layer.

The public KeyVal provider does not require authentication. The token option is
for private KeyVal-compatible providers only.

## Proxy Health-Check Configuration

Add typed constants for the environment names:

```python
PROXY_TEST_TARGET_URL_ENV_NAME_STR = "PROXY_TEST_TARGET_URL"
PROXY_MAX_TIMING_MILLISECOND_ENV_NAME_STR = "PROXY_MAX_TIMING_MILLISECOND"
```

Application behavior must be:

1. Resolve `PROXY_TEST_TARGET_URL` from the environment or `.env`.
2. Fall back to `PROXY_TEST_TARGET_URL_STR` when it is blank or missing.
3. Resolve `PROXY_MAX_TIMING_MILLISECOND` as an integer.
4. Fall back to `PROXY_MAX_TIMING_MILLISECOND_INT` when it is missing or
   invalid.
5. Clamp the resolved timing value to at least one millisecond.
6. Use the timing value for both the health-check request timeout and the
   service rule that rejects slow proxies.

## Environment Helper

Keep environment parsing generic and reusable in:

```text
core/helper/env_value_helper.py
```

Provide an integer resolver such as:

```python
getEnvIntValue(envNameStr, defaultValueInt, envFilePathStr=".env")
```

The `.env` parser must support inline comments. For example, this must resolve
as a blank value rather than the literal comment text:

```text
KEY_VAL_BASE_URL= # Optional setting.
```

Do not add provider-specific behavior to the helper layer.

## Application Entry Point

Update:

```text
app/key_value_proxy_app.py
```

Expose a testable builder such as:

```python
buildVerboseElasticIpPoolService(envFilePathStr=".env")
```

The builder should:

- resolve all supported environment configuration
- construct `KeyValStoreProxy` only when external persistence is enabled
- construct `ElasticIpHealthCheckProxy` with the configured target and timeout
- pass the maximum timing value into `VerboseElasticIpPoolService`
- preserve service, repo, and proxy layer boundaries

The entry point must not make external API calls directly.

## Logging

When KeyVal persistence is disabled, verbose output should state that external
cache persistence is disabled.

Only log the redacted KeyVal cache URL when cache reads are enabled. Continue
redacting proxy network locations, KeyVal paths, storage keys, and sensitive
values.

## Raw Proxy Contract

Because `KeyValStoreProxy` request headers change, update:

```text
raw/proxy/key_val_store_proxy/request.txt
raw/proxy/key_val_store_proxy/json/input.json
raw/proxy/key_val_store_proxy/json/output.json
```

Document the optional bearer header using placeholders only. Raw examples must
not contain real tokens, credentials, proxy passwords, private IPs, or other
sensitive data. Both JSON files must remain valid JSON.

## Documentation

Update `README.md` to explain:

- the four environment variables
- blank `KEY_VAL_BASE_URL` disables external cache persistence
- nonblank `KEY_VAL_BASE_URL` enables KeyVal-compatible cache reads and writes
- `KEY_VAL_AUTH_TOKEN` is optional and intended for private providers
- `PROXY_TEST_TARGET_URL` controls the validation endpoint
- `PROXY_MAX_TIMING_MILLISECOND` controls timeout and accepted latency
- `keyValStoreProxyStr` remains the compatible KeyVal key source
- `app/key_value_proxy_app.py` is the supported manual entry point

Remove documentation for obsolete entry points or runner files that no longer
exist.

## Tests

Use mocked, offline tests only. Do not call live KeyVal, proxy providers,
Firebase, or health-check endpoints.

Cover at least:

1. Blank `KEY_VAL_BASE_URL` disables cache reads and writes in the app.
2. A configured KeyVal base URL enables cache reads and writes.
3. A configured bearer token is added to KeyVal requests.
4. A blank token omits the `Authorization` header.
5. The configured health-check target reaches `ElasticIpHealthCheckProxy`.
6. The configured timing value reaches both the health-check proxy and service.
7. Invalid integer configuration falls back safely.
8. Inline comments after blank `.env` values are ignored.
9. Raw example JSON remains valid.
10. No obsolete test imports removed runner modules.

Run:

```bash
python3 -m unittest discover -s test -p "test_*.py"
python3 -m json.tool raw/proxy/key_val_store_proxy/json/input.json
python3 -m json.tool raw/proxy/key_val_store_proxy/json/output.json
git diff --check
```

## Architecture Requirements

Maintain this flow:

```text
App Entry Point -> Service -> Proxy -> External API
App Entry Point -> Service -> Repo -> Storage
```

- Constants contain only typed constants.
- Helpers contain only generic reusable parsing behavior.
- Proxies own provider URLs, headers, authentication, and HTTP requests.
- Services own proxy selection and accepted-timing business rules.
- Repos own storage behavior.
- The app only resolves configuration and composes dependencies.

## Completion Checklist

Before finishing, verify:

- All four environment variables are supported.
- `env_example` uses inline comments.
- Blank KeyVal configuration performs no KeyVal network calls.
- Bearer authentication remains optional and secret-safe.
- Proxy target and maximum timing configuration are applied consistently.
- N-layer boundaries pass review.
- KeyVal raw request/input/output examples match the proxy implementation.
- Raw JSON files are valid.
- No secrets or real `.env` values are committed.
- The complete offline unit-test suite passes.
