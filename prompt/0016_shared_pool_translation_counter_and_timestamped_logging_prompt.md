# 016 - Shared Pool Translation Counter and Timestamped Logging

Follow `AGENTS.md` and `skill/service-boundary-review/SKILL.md` for implementation
work. Follow `skill/proxy-example-contract/SKILL.md` if a proxy class changes.

## Scope and Baseline

Capture the package changes made after the final follow-up in prompt 0015,
`0015_cached_proxy_translation_counter_info_logging_prompt.md`, last updated in
commit `a2312db`. These changes already exist in the package:

- `fe991cf`: shared translation counter and revised rediscovery rules.
- `c873018`: timestamped logging, reliable total runtime, and version `1.0.6`.

This prompt is a handoff for preserving and verifying that behavior, not a
request to reimplement it. Creating this prompt does not authorize another
version bump, consumer changes, live database writes, publishing, or a commit
and push. Keep this documentation update limited to the new prompt file.

Where they conflict, the requirements below supersede prompts 0013–0015:
per-proxy counter isolation, the default lower threshold of `-5`, resetting
every returned proxy separately, excluding fresh candidates because of the
translation counter, bracket-only log prefixes, the `[run] took` summary, and
the instruction to retain package version `1.0.5`.

## One Shared Counter and Stable Storage Key

Use one signed translation counter for the entire proxy list. Completed
subtitle successes add one; explicitly proxy-caused failed attempts subtract
one, regardless of which proxy in the list was used. This remains a net count,
not a total-success count or consecutive-failure count.

- Derive the key as the SHA-256 hash of the literal variable name
  `keyValProxyTranslationCountKeyStr`, defined by
  `KEY_VAL_PROXY_TRANSLATION_COUNT_VARIABLE_NAME_STR`.
- Expose `getKeyValProxyTranslationCountKey()` without requiring an address.
  Keep its optional `proxyStr` argument for existing callers; validate a supplied
  non-None address, but do not incorporate it into the key.
- Changing proxy addresses, ports, ranked-list contents, the proxy-cache
  namespace, or the legacy counter namespace must not change this key.
- Keep `KEY_VAL_PROXY_TRANSLATION_COUNT_KEY` and the
  `keyValProxyTranslationCountKeyStr` constructor argument accepted for
  compatibility. They no longer control counter storage identity.
- All instances using the same KeyVal database share the counter, even if their
  proxy-cache namespaces differ. Local-only state remains in the service
  instance; it is not distributed between instances without persistence.
- Keep the counter key separate from the proxy-cache key. Store plain signed
  decimal text, such as `0`, `1`, `50`, or `-3`.
- Do not read, aggregate, migrate, or delete the old per-proxy counter records.
  If the new shared key is absent, use the established zero-initialization flow.

Preserve the public counter getters and feedback API. The actual attempted
proxy is still required for feedback validation and consumer correlation, but
different valid endpoints now update the same counter. Reject invalid feedback
addresses and contradictory success/proxy-failure flags before writing.

## Pool Thresholds and Fresh Discovery

Keep the upper default at `50`; change the lower default to `-3`. Preserve
constructor-over-environment-over-env-file precedence and safe fallback for
missing, blank, malformed, or wrong-sign environment limits. Update the README
and `env_example` to explain both defaults and the legacy namespace setting.

1. Before validating a saved list, observe the shared counter. At `>= 50` or
   `<= -3`, reject cached reuse, including persisted overshoots after restart.
   `check()` returns no cached proxy; `get()` / `run()` can proceed to discovery.
2. Separate historical resource eligibility into
   `isProxyHistoryUsageAllowed(proxyStr)`. Cached-list iteration and fresh
   candidate preparation/validation use the per-proxy history rules; an
   exhausted shared translation counter must not exclude all fresh candidates.
   Keep `isProxyUsageAllowed(proxyStr)` combining the shared limit and history
   checks for callers that need both.
3. Preserve Firebase disabled-resource and historical usage-limit rules. They
   remain per proxy and separate from the shared subtitle counter.
4. After successful fresh discovery has selected and ranked a working list,
   reset and verify the shared counter exactly once, using the selected proxy
   with the existing reset method. Do not loop over every ranked proxy to reset
   the same key repeatedly. Apply this to fallback-provider discovery and
   threshold-triggered discovery as well.
5. Previously selected addresses may reappear after fresh discovery if they
   pass health validation and historical usage checks. The shared threshold
   ends a pool cycle; it does not permanently disable those endpoints.
6. Failed or empty discovery does not reset the counter. Preserve an exhausted
   value and return `None` when no usable result exists; clear stale result state.
7. Preserve immediate rediscovery as the feedback API default. With
   `rediscoverBool=False`, record feedback without a mid-subtitle search and
   enforce the limit at the next pool lookup. Returning the same address from
   deferred feedback is not a recommendation to keep using it.
8. Once the current shared value is at a limit, later feedback must not move it
   back into the usable range. Only successful fresh discovery starts a new cycle.

Preserve prompt 0015's verified initialization of confirmed missing/null/empty
values, observational internal reads, preservation of existing numeric values
on cache reuse, read-only settings, and local fallback after storage failures.
Do not treat network errors or malformed values as permission to overwrite the
database. Health checks and selection are not translation outcomes; successful
fresh discovery has the separate explicit reset rule above.

KeyVal read/modify/write is not atomic. Document the single-reporting-worker
limitation per KeyVal database, replacing the previous per-namespace guidance.
Different cache namespaces no longer isolate concurrent counter writers.

## Timestamped Package Logs

Use this format for every physical package log line, including multiline output:

```text
YYYY-MM-DD HH:MM:SS,mmm | LEVEL | n-elastic-ip-pool | message
```

- Set `CORE_LOGGER_NAME_STR` to `n-elastic-ip-pool` and define
  `LOGGER_FORMAT_STR = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"`.
- Use the generic `formatLogMessage` helper in
  `core/helper/log_message_format_helper.py` to format a `logging.LogRecord`
  through `logging.Formatter`, without configuring application/root handlers.
- Keep the verbose service's shared `logMessage` path and existing level
  filtering. Format and print each physical line separately. Timestamps use
  local date/time with milliseconds.
- Add `scope=pool` to counter read/write field logs. A `proxy=` field identifies
  the associated endpoint, not a separate counter owner.
- Preserve source, event, persistence, credential-redaction, and cache-value
  semantics from prompt 0015. Keep configuration and individual validation
  details at DEBUG. Keep selected proxy, cache state, and counter state at INFO.
- Preserve summary deduplication: cache-hit selection/list summaries appear
  under `[cache]`; discovery selection/list summaries appear under `[run]`.

Safe illustrative output:

```text
2026-08-30 18:55:54,969 | INFO | n-elastic-ip-pool | [translation-count] key=<hashed-counter-key> count=0 source=keyval event=write stored=true scope=pool
2026-08-30 18:55:54,970 | INFO | n-elastic-ip-pool | [translation-count] key=<hashed-counter-key> count=12 source=keyval event=read proxy=proxy-one.example.net:8080 scope=pool
2026-08-30 18:55:54,971 | INFO | n-elastic-ip-pool | Total run time: 22.56 seconds operation=run
```

## Total Runtime on Success and Failure

Wrap `VerboseElasticIpPoolService.run()` around `_runDiscovery()` with a
`try/finally`. Measure elapsed time with `time.perf_counter()` and emit one
INFO summary in this form:

```text
Total run time: <seconds with two decimal places> seconds operation=run
```

Clamp elapsed time to a nonnegative value. Emit the summary after a cache hit,
successful discovery, an empty result, or a raised discovery error. Preserve
the return value or original exception. Respect quiet log levels, so they do
not gain an unconditional print. Remove the old `[run] took` summary while
retaining separate discovery timing diagnostics. This total-runtime wrapper
applies to `run()`; do not claim standalone `get()` / `check()` / `search()`
calls execute it.

## Verification and Package State

The package metadata and README now identify version `1.0.6`. Preserve that
version for this handoff; do not repeat the earlier `1.0.5` release constraint.

Existing offline regression coverage was updated in:

- `test/service/test_proxy_translation_feedback_service.py`: stable shared
  key across addresses and namespaces, default/explicit limits, exact thresholds
  and overshoots, exhausted-cache rejection with fresh candidate validation,
  one reset for a changed working list, feedback shared across service instances,
  failed rediscovery, fallback discovery, storage outages, invalid feedback,
  late-result handling, and counter logs with `scope=pool`.
- `test/service/test_verbose_elastic_ip_pool_service.py`: timestamped INFO/DEBUG
  and multiline formatting, summary deduplication, and exactly one total-runtime
  summary on failure while preserving the original exception.

For any future implementation changes, run the complete offline suite, inspect
the diff, and verify package metadata/build/import behavior as appropriate.
Do not reuse prompt 0015's historical test counts as verification of these later
changes. This documentation-only update does not assert a new test run, build,
publication, live KeyVal verification, or external translator verification.

Boundary review of the two recorded commits: PASS. Counter and rediscovery
rules stay in the service; formatting is a generic helper; constants hold
configuration values; existing proxy/repo abstractions remain in place. No new
boundary violations, file moves, or refactors are required for these changes.
No provider proxy class changed, so no raw request/response contract update was
needed. If future work changes one, update all matching safe raw examples.

Do not modify the external no-driver-translate consumer as part of this prompt
capture. Its previous single-lookup/deferred-feedback workflow remains relevant,
but old assertions about isolated per-endpoint counters are superseded by the
shared-counter contract. Never copy production logs, credentials, private
infrastructure, or sensitive provider data into this package.
