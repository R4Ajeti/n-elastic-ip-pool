# 015 - Professional Package Logging and KeyVal Proxy/Counter Verification

Follow `AGENTS.md` and `skill/service-boundary-review/SKILL.md` when changing
implementation. This prompt consolidates all user clarifications for the logging
changes delivered in version `1.0.5`.

## Goal

Make logs clean, consistent, and easy to search. At INFO, show the actual KeyVal
keys and values for both the saved proxy list and the selected proxy's subtitle
translation counter, including runs that reuse cached proxies without updating
the counter. Configuration output alone is not sufficient for database verification.

## Unique Package Prefix

Every package log line must start with one of:

```text
[n-elastic-ip-pool] [INFO]
[n-elastic-ip-pool] [DEBUG]
```

Use `CORE_LOGGER_PREFIX_STR` and the shared `logMessage` formatter. Prefix every
physical line of multiline messages. Keep the existing level filtering and
logging configuration precedence. Remove duplicate unprefixed result prints
from the app entry point; its service already logs the final result.

Search keywords:

- `n-elastic-ip-pool`: every package log line.
- `[translation-count]`: subtitle counter keys, values, and persistence state.
- `[proxy-cache]`: the saved proxy variable, storage key, and value.
- `[run] selected proxy:`: the proxy returned to the caller.

## Clean Startup Summary

Keep INFO summaries short and separate selection, validation, and limits:

```text
[n-elastic-ip-pool] [INFO] [run] selection: mode=fastest resultCount=all
[n-elastic-ip-pool] [INFO] [run] validation: passes=3 maxTimingMs=2000
[n-elastic-ip-pool] [INFO] [run] limits: translationMaxUseCount=50 translationMinHealthCount=-5 historicalUsageLimit=100
```

`historicalUsageLimit=100` belongs to the older Firebase usage-history contract,
not the subtitle counter. Keep `[run] options` (release channel, candidate limit,
shuffle, cache/save flags) and repetitive setup notes at DEBUG. Do not change
selection behavior or either set of limits as part of logging cleanup.

## Translation Counter Logging

Log the selected proxy's exact hashed counter key and current count after a
successful cached lookup through `run()`, `get()`, or `check()`, and after fresh
`search()` selects a proxy. Continue logging counter writes after a reset or
reported translation result. Use one counter-line formatter for reads and writes.

```text
[n-elastic-ip-pool] [INFO] [translation-count] key=<counter-key> count=12 source=keyval event=read proxy=proxy-one.example.net:8080
[n-elastic-ip-pool] [INFO] [translation-count] key=<counter-key> count=0 source=keyval event=write stored=true
```

Interpret fields accurately:

- `key`: the actual KeyVal lookup key, not its unhashed configuration source.
- `count`: the effective signed translation count.
- `source=keyval`: a successful database read, or an acknowledged database write.
- `source=missing`: no stored counter exists; the effective count is zero.
- `source=local`: local-only or unsaved state.
- `source=local-fallback`: a failed/invalid read required using local state.
- `event=read` / `event=write`: distinguish lookup from update.
- `stored=true` / `stored=false`: include for write events only; do not imply
  that a failed or disabled write reached the database.
- `proxy`: credential-redacted selected address on read events.

Expose `getProxyTranslationCountState(proxyStr)` for the key, count, and source,
while preserving the integer-returning `getProxyTranslationCount(proxyStr)` API.
Do not reset, increment, or persist a counter just to display it. Quiet log levels
must not trigger an extra read solely for display. If a run selects no proxy, log:

```text
[n-elastic-ip-pool] [INFO] [translation-count] no selected proxy; no counter to display
```

Preserve prompt 0014's reset behavior: successful fresh discovery starts returned
working proxies at zero; cached checks and failed searches do not reset counters.

## Saved Proxy Logging

At INFO, show the proxy-cache configuration variable name, actual hashed cache
key, and credential-redacted stored proxy list when read or successfully saved:

```text
[n-elastic-ip-pool] [INFO] [proxy-cache] variable=keyValStoreProxyStr key=<proxy-cache-key> value=["proxy-one.example.net:8080"] source=keyval event=read state=stored-value
[n-elastic-ip-pool] [INFO] [run] selected proxy: proxy-one.example.net:8080
```

`variable=keyValStoreProxyStr` identifies the key-source configuration variable;
it must not expose the unhashed namespace. `key=` is the actual database key.
Keep proxy-cache keys distinct from per-proxy translation-counter keys.

The cache value is a stored snapshot, not a claim that every saved proxy works.
Retain separate working-proxy summaries containing only currently validated
entries. Mark missing/unavailable reads explicitly. Malformed cached values must
not make logging fail. Never expose credentials, bearer tokens, sensitive URL
paths/query strings, or full KeyVal request URLs.

## Verification Instructions for the User

Enable INFO output with `DEBUGGING=false` or `LOGGER=INFO` on the verbose service,
respecting the existing precedence of `DEBUGGING` when set. Search logs for
`n-elastic-ip-pool`, then narrow to `[proxy-cache]` or `[translation-count]`.
Copy the relevant exact `key=` value into the configured KeyVal database lookup.
Compare the saved value with `value=` for proxies or `count=` for translations.
Local/fallback values are not verified database values.

## Verification and Release

Use offline tests only. Cover cached run/get/check output, fresh-discovery output,
stored and missing counters, failed reads, local fallback, quiet levels, no proxy
selected, cache read/write values, credential redaction, malformed URLs, package
prefixes on every line, and removal of duplicate entry-point prints.

Check architecture boundaries, update README examples, run the complete test
suite, check the diff, and build/import-test the package. The implementation was
released as `1.0.5` in commit `6df3ef3`: 147 tests passed with 2 pre-existing skips.
Commit and push implementation changes as requested. Documentation-only updates
to this prompt do not require another package version bump.
