# 009 - Firebase Proxy Usage History Storage

Follow `AGENTS.md` and the relevant repository skills before making changes.

Implement configurable Firebase-backed storage for proxy usage history and usage counts. This should be an optional storage backend that is enabled only when the expected environment variables are present.

## Goal

Add a safe way to use either Firebase Firestore or Firebase Realtime Database to store:

- historic proxy usage records
- per-proxy usage counts
- disabled/unavailable state when a proxy has been used too many times

The Elastic IP pool service must use historic usage data when deciding whether a proxy can be returned.

## Environment Configuration

Add typed constants for all environment variable names:

- `FIREBASE_DATABASE_TYPE_ENV_NAME_STR`
- `FIREBASE_FIRESTORE_KEY_BASE64_ENV_NAME_STR`
- `FIREBASE_REALTIME_DATABASE_KEY_BASE64_ENV_NAME_STR`
- `FIREBASE_REALTIME_DATABASE_URL_ENV_NAME_STR`

Supported database type values:

- `firestore`
- `realtime_database`

If a matching base64 credential environment variable is available, decode it safely at runtime. The encoded value should contain a Firebase service-account JSON object or another clearly documented Firebase credential payload.

Do not commit:

- decoded Firebase credentials
- encoded Firebase credentials
- `.env` files
- real Firebase service-account JSON
- tokens, API keys, private keys, private URLs, or project secrets

## Constants

Add typed constants for usage limits and Firebase selection values, for example:

- `FIREBASE_DATABASE_TYPE_FIRESTORE_STR`
- `FIREBASE_DATABASE_TYPE_REALTIME_DATABASE_STR`
- `MAX_PROXY_USAGE_COUNT_INT`
- `DEFAULT_FIREBASE_COLLECTION_NAME_STR`
- `DEFAULT_FIREBASE_USAGE_HISTORY_PATH_STR`

`MAX_PROXY_USAGE_COUNT_INT` must control when historic usage makes a proxy unavailable. If a proxy's stored usage count is greater than or equal to this constant, the service must skip it or mark it disabled.

## Architecture Rules

Keep N-layer boundaries clean:

- Service layer owns business rules.
- Repo layer owns storage access and hides Firebase implementation details.
- Helper layer may contain only generic reusable decoding or JSON parsing utilities.
- Constant layer contains only constants.
- Proxy layer remains for external proxy/provider APIs and should not decide Firebase usage rules.

The service layer should:

- choose whether a proxy is usable
- record successful proxy usage
- increment historic usage count
- read historic usage count through a repo interface
- disable or skip proxies that reached `MAX_PROXY_USAGE_COUNT_INT`
- return no available proxy when every candidate is disabled, failed, or overused

The repo layer should:

- abstract Firestore and Realtime Database storage details
- expose clean domain methods such as `getProxyUsageCount`, `recordProxyUsage`, and `markProxyDisabled`
- handle missing Firebase configuration with placeholder-safe behavior
- avoid business decisions about whether a proxy should be selected

The helper layer may:

- decode base64 strings
- parse JSON strings
- return safe error values for invalid encoded input

The helper layer must not:

- know Firebase collection names
- know Firebase database paths
- choose which Firebase backend to use
- decide whether a proxy is disabled

## Storage Behavior

When Firebase configuration is present:

1. Decode the configured base64 credential value.
2. Initialize the selected Firebase backend through repo-owned storage code.
3. Store a usage-history entry each time a proxy is successfully used.
4. Increment the proxy's usage count.
5. Store disabled state when usage reaches `MAX_PROXY_USAGE_COUNT_INT`.

When Firebase configuration is missing or invalid:

1. Do not crash normal proxy selection.
2. Fall back to the existing in-memory or placeholder-safe repo behavior.
3. Make the missing configuration observable through a return status, exception caught by the service, or logger-safe message.
4. Do not make network calls in tests.

Use safe sample proxy values in tests and docs, such as:

- `proxy-one.example.net:8080`
- `proxy-two.example.net:8080`
- `203.0.113.10:8080`

Do not use real public proxy endpoints or private IP addresses.

## Suggested Files

Add or update files along these lines, matching the existing codebase style:

- `core/constant/elastic_ip_pool_constant.py`
- `core/helper/base64_json_helper.py`
- `core/repo/elastic_ip_pool_repo.py`
- `core/repo/firebase_proxy_usage_history_repo.py`
- `core/service/elastic_ip_pool_service.py`
- `test/constant/test_elastic_ip_pool_constant.py`
- `test/helper/test_base64_json_helper.py`
- `test/repo/test_firebase_proxy_usage_history_repo.py`
- `test/service/test_elastic_ip_pool_service.py`

Use singular naming, snake_case file names, PascalCase classes, camelCase methods, and typed UPPER_SNAKE_CASE constants.

## Tests

Add mocked or placeholder-safe unit tests only. Tests must not require:

- real Firebase credentials
- real Firebase projects
- internet access
- live Firestore calls
- live Realtime Database calls
- real proxy providers

Cover at least:

1. Base64 JSON helper decodes valid base64 JSON.
2. Base64 JSON helper safely handles missing or invalid encoded values.
3. Firebase repo chooses Firestore when `FIREBASE_DATABASE_TYPE_ENV_NAME_STR` is `firestore`.
4. Firebase repo chooses Realtime Database when `FIREBASE_DATABASE_TYPE_ENV_NAME_STR` is `realtime_database`.
5. Missing Firebase env vars fall back to placeholder-safe behavior.
6. Service records successful proxy usage through the repo.
7. Service skips or disables a proxy when historic usage count reaches `MAX_PROXY_USAGE_COUNT_INT`.
8. Service returns no available proxy when all candidates are failed, disabled, or overused.
9. Tests use mocks/stubs and never call real Firebase or external proxy endpoints.

Run:

```bash
python3 -m unittest discover -s test -p "test_*.py"
```

## Completion Checklist

Before finishing:

- Verify N-layer structure is respected.
- Verify constants use UPPER_SNAKE_CASE with type suffixes.
- Verify service owns usage-count business decisions.
- Verify repo owns Firebase storage access.
- Verify helpers remain generic and reusable.
- Verify no real credentials or `.env` files are committed.
- Verify tests do not make live network calls.
- Verify overused proxies are disabled or skipped using `MAX_PROXY_USAGE_COUNT_INT`.
