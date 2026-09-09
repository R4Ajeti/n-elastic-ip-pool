# Optional Sentry Logs implementation plan

## Inspection

- `n-proxy` uses `VerboseElasticIpPoolService.logMessage` to print already-redacted messages; its public package maps `core` into `n_elastic_ip_pool`.
- `n-user-agent` uses the shared `n-user-agent-pool` Python logger plus a separate verbose output callback. Its logger helper preserves quiet defaults and local level controls.
- `no-driver-translate` uses both `no_driver_translate.*` and `no-driver-translate` loggers, configured by `runtime_logging`. It consumes both pool packages in the same process.
- All working trees were clean at inspection. Follow repository architecture/raw-example rules and keep tests offline; do not run live translation benchmarks.

## Shared contract

- `SENTRY_DSN`: opt-in destination; blank/unset means no SDK initialization or transmission. No auth token is necessary for ingestion.
- `SENTRY_ENVIRONMENT`: optional deployment label, default `development`.
- `SENTRY_RELEASE`: optional release label; omitted when blank.
- `SENTRY_LOG_LEVEL`: minimum remote severity, default `INFO`; support DEBUG/INFO/WARNING/ERROR/CRITICAL and WARN, fall back to INFO on invalid input.
- Fixed `SENTRY_REPOSITORY_NAME_STR` values: `n-proxy`, `n-user-agent`, `no-driver-translate`. Add `repository` and `service.name` log attributes without changing existing console names.
- Add `sentry-sdk>=2.35.0,<3` runtime dependency, supporting stable Sentry Logs options and public scoped logging APIs.
- Each repository owns a lazy isolated SDK client with default integrations disabled. Do not replace the host application's global Sentry client or automatically collect unrelated loggers/errors/traces. Use the public Sentry logger API within a temporary scope bound to that client.
- Preserve local output and its existing level gates. Remote threshold additionally filters emitted messages. SDK configuration failures warn once without exposing values and leave local work operational. Flush buffered logs at normal interpreter shutdown.

## Sequential implementation

1. n-proxy: constants and provider adapter in the constant/proxy layers; forward verbose messages after existing redaction. Support its existing env-file path as well as exported configuration. Add safe raw contracts, offline tests, README and env_example documentation.
2. n-user-agent: matching constants/provider adapter; attach one handler to the shared logger during service construction and forward explicit verbose output. Preserve console handler configuration and avoid duplicates. Update raw contracts, tests, README and `.env.example` (the existing sample filename).
3. no-driver-translate: matching adapter/constants; attach handlers to both project logger namespaces from runtime logging initialization, including Sentry-only library configuration. Update tests, README and env_example.

## Verification

Test disabled/blank config, configured delivery and repository attributes, severity filtering, invalid configuration, repeated setup, formatted/verbose forwarding and preservation of a host SDK client. Use an in-memory Sentry transport to verify actual log envelopes without network calls. Run each repository's deterministic test suite and inspect diffs/package metadata/raw JSON. Verify coexistence of all three labels in a single process.

## SDK references

- https://docs.sentry.io/platforms/python/logs/
- https://getsentry.github.io/sentry-python/api.html

## Implementation and verification result

Completed sequentially: n-proxy, n-user-agent, then no-driver-translate.
README and the existing environment sample are updated in each repository.
The translation CLI environment allowlist now includes all four Sentry settings.

- n-proxy: 172 passed, 2 existing skips (plus 88 subtests).
- n-user-agent: 97 passed (plus 20 subtests).
- no-driver-translate: 252 passed, 2 pre-existing failures (plus 145 subtests).
- All 25 new Sentry tests pass. The adapter was exercised with SDK 2.35.0 and 2.69.1; actual log envelopes were collected with in-memory transports.
- A single-process offline check verified all three distinct repository labels.
- All three wheel builds succeeded; wheel inspection verified Sentry modules and dependency metadata. Safe raw JSON examples parse successfully. git diff --check passes.
- Architecture review: PASS. SDK communication remains in pool proxy layers and the translation runtime adapter; helpers remain generic. No architecture violations or additional moves/refactors required.
- No live Sentry requests or live browser benchmarks were used for validation.

The existing failures are in tests/test_subtitle_proxy_feedback.py:
`test_configured_attempt_limit_does_not_refetch_or_use_extra_routes` and
`test_three_attempts_one_lookup_and_actual_proxy_counters`. Both also fail with
untouched HEAD archives of n-proxy and no-driver-translate: those tests expect
individual proxy counters while the local n-proxy implementation uses a shared
pool counter. They were left outside the Sentry change.
