# 015 - Professional Package Logging and KeyVal Proxy/Counter Verification

Follow `AGENTS.md` and `skill/service-boundary-review/SKILL.md` when changing
implementation. This prompt consolidates all user clarifications for the logging
changes, including the missing-counter and DEBUG-only corrections below.
The user subsequently authorized fixing null/missing counters: initialize them
to zero. Implement the missing-counter and DEBUG-only logging corrections below,
keeping the package version at `1.0.5`. Do not change the external translator.
Latest clarification: public counter reads must immediately initialize and verify
a missing/null/empty counter, not wait until a proxy has been selected. Apply
this to `getProxyTranslationCount` and `getProxyTranslationCountState` as well
as `ensureProxyTranslationCount`, respecting explicit read-only settings. Keep
internal candidate eligibility reads observational to avoid initializing unused
provider candidates. Separate observational reads from initialization to prevent
recursive write/read-back loops. Merely opening a KeyVal GET URL in a browser
does not run this package or create the record.

## Goal

Make logs clean, consistent, and easy to search. At INFO, show the actual KeyVal
keys and values for both the saved proxy list and the selected proxy's subtitle
translation counter, including runs that reuse cached proxies. Ensure a missing
counter is initialized in KeyVal when persistence is enabled; an effective local
zero alone is not sufficient for database verification. Preserve existing counts
on cached lookups. Configuration output alone is not sufficient.

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

## DEBUG-Only Configuration and Validation Details

Move all of these categories to DEBUG. They must not appear at INFO:

```text
[n-elastic-ip-pool] [DEBUG] [run] selection: mode=fastest resultCount=all
[n-elastic-ip-pool] [DEBUG] [run] validation: passes=3 maxTimingMs=2000
[n-elastic-ip-pool] [DEBUG] [run] limits: translationMaxUseCount=50 translationMinHealthCount=-5 historicalUsageLimit=100
[n-elastic-ip-pool] [DEBUG] [run] validated proxy: proxy-one.example.net:8080 averageTimingMs=333 successCount=1 checkedAt=2026-01-01T00:00:00Z
```

Apply this to every per-proxy `[run] validated proxy:` timing/success/timestamp
line, not only the example. Keep the selected proxy, proxy-cache key/value, and
translation-counter key/value visible at INFO.

`historicalUsageLimit=100` belongs to the older Firebase usage-history contract,
not the subtitle counter. Keep `[run] options` (release channel, candidate limit,
shuffle, cache/save flags) and repetitive setup notes at DEBUG. Do not change
selection behavior or either set of limits as part of logging cleanup.

## Missing Counter Must Be Initialized

The user observed `count=0 source=missing event=read` while looking up the same
key in KeyVal returned:

```json
{"status":"-KEY-DOESNT-EXISTS-","key":"<counter-key>","val":""}
```

These agree that the key is absent: the logged zero was an effective fallback,
not a saved value. Merely printing the computed key does not create its record.

Required correction:

1. After selecting a validated proxy, check its counter using the exact same
   derived key, provider, and authentication used for subsequent translation
   feedback. Cover cached `run()` / `get()` / `check()` as well as discovery.
2. If the counter is confirmed missing and writes are enabled, create it with
   the plain numeric text `0`. Handle the provider's missing-key response above,
   not just HTTP 404. Do not create records for every rejected candidate.
3. Read the newly created key back and verify the numeric value before showing
   the final selected-counter INFO line as a verified KeyVal read. A successful
   fallback calculation or an attempted write is not proof of persistence.
4. Preserve existing counters, including valid zero and negative values. Repeated
   cached lookups must not reset, increment, or overwrite them. Only successful
   fresh discovery follows the separate reset rule from prompt 0014.
5. Do not interpret a network error, authentication error, malformed response,
   or invalid counter value as confirmed absence and overwrite it with zero.
6. Respect read-only/local-only settings. If creation or verification fails,
   retain safe local behavior and explicitly report missing/local/unverified
   state. Never claim that a failed write created a database record.
7. Put initialization in the service workflow, not the logging formatter, so it
   works at every log level and in the non-verbose service. Keep HTTP behavior
   behind `KeyValStoreProxy`. If that proxy changes, follow the proxy-example
   contract skill and update its safe raw request/input/output examples.

Successful initialization should allow the user to retrieve `0` using the exact
logged key from the same KeyVal database. Preserve the existing documented
single-writer limitation; do not claim atomic initialization for a provider that
does not support it.

## Additional Consumer Run Evidence

The user later supplied mixed logs from the consuming subtitle translator and
this package. Preserve the following findings without committing the production
log dump, local browser profile paths, live proxy addresses, or production keys:

- The package logged a saved-cache lookup and selected a cached proxy. The
  `Proxy discovery run` banner does not prove fresh discovery occurred: there
  were no provider-search messages in this excerpt. Therefore the fresh-search
  reset path did not initialize the selected cached proxy's missing counter.
- The selected proxy's counter again logged `count=0 source=missing event=read`.
  No counter-write event appears in the supplied excerpt. This supports the
  missing-initialization problem, but does not prove that the consuming app
  never calls the feedback method elsewhere.
- The consuming translator subsequently retried a different address from the
  pool and reported a proxy-tunnel connection failure on its final attempt.
  A proxy passing the configured health check is not a guarantee that it can
  establish a connection to the translator's target.
- The same host with different ports represents distinct proxy endpoints and
  therefore distinct counters. Use the key for the exact host:port actually
  used by the translation attempt, not a key from a previous selected endpoint.

When implementation/integration work is authorized, verify that the consumer
reports confirmed proxy-caused failures against the proxy actually used:
`recordSubtitleTranslationResult(attemptProxyStr, successBool=False,
proxyFailureBool=True)`. Report the final failed attempt too, exactly once;
avoid counting both the retry handler and the final exception handler for the
same failure. Report success only after the whole subtitle successfully completes,
not after a browser launch, listener installation, or pool health check.

Ensure the consumer honors the returned next proxy or `None` and does not silently
keep using a stale selected address. If it explicitly chooses another ranked
candidate for an attempt, associate initialization and feedback with that actual
candidate, without initializing every unused candidate just for logging.
Keep logs able to correlate the attempted address with its counter key and update.

This repository does not contain the consuming translator. Do not claim that its
feedback wiring has been inspected or fixed based only on these logs. Do not
expand this task into browser flags, user-agent behavior, restriction bypass, or
changes to live translation retry behavior without a separate authorized request.

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
- `source=missing`: no stored counter exists; any displayed zero is an effective
  fallback, not a persisted value. With writable persistence, attempt the
  workflow initialization above before the final selected-counter summary.
- `source=local`: local-only or unsaved state.
- `source=local-fallback`: a failed/invalid read required using local state.
- `event=read` / `event=write`: distinguish lookup from update.
- `stored=true` / `stored=false`: include for write events only; do not imply
  that a failed or disabled write reached the database.
- `proxy`: credential-redacted selected address on read events.

Expose `getProxyTranslationCountState(proxyStr)` for the key, count, and source,
while preserving the integer-returning `getProxyTranslationCount(proxyStr)` API.
Do not reset, increment, or persist a counter merely inside a logging method.
Missing-counter initialization is an explicit service-workflow responsibility,
independent of log level. Quiet log levels must not trigger an extra read solely
for display, but must still perform required workflow initialization and its
verification. If a run selects no proxy, log:

```text
[n-elastic-ip-pool] [INFO] [translation-count] no selected proxy; no counter to display
```

Preserve prompt 0014's reset behavior: successful fresh discovery starts returned
working proxies at zero; cached checks preserve existing counters and initialize
only genuinely missing ones. Failed searches do not reset counters.

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
Local/fallback values are not verified database values. A missing-key response
means initialization did not occur or did not persist; it is not a stored zero.
Turn DEBUG on only when configuration details or individual proxy timings are
needed; those details must not clutter normal INFO output.

## Verification and Release

Use offline tests only. Cover cached run/get/check output, fresh-discovery output,
stored and missing counters, failed reads, local fallback, quiet levels, no proxy
selected, cache read/write values, credential redaction, malformed URLs, package
prefixes on every line, and removal of duplicate entry-point prints.

Add regression coverage for the reported problem:

- A cached working proxy with a missing counter gets a `0` record in a writable
  fake KeyVal store, and the final logged key retrieves that value.
- HTTP-200 `-KEY-DOESNT-EXISTS-` and HTTP-404 absence are handled correctly.
- Existing positive, zero, and negative counters remain unchanged on cache use.
- Failed reads, invalid values, rejected writes, failed read-back verification,
  read-only settings, and local-only settings never falsely claim persistence.
- Initialization works with INFO, DEBUG, quiet levels, and the base service.
- INFO omits `[run] selection:`, `[run] validation:`, `[run] limits:`, and every
  `[run] validated proxy:` detail. DEBUG includes them with the package prefix.
- INFO still shows selected proxy, cache key/value, and counter key/value.
- A simulated consumer failure updates only the actual attempted proxy's counter,
  even when it differs from the last selected proxy or uses another port on the
  same host. A final failed attempt is reported once, without duplicate updates.
- Cached selection remains distinguishable from fresh provider discovery; logging
  a run banner alone must not be treated as a reset/initialization event.

Check architecture boundaries, update README examples, run the complete test
suite, check the diff, and build/import-test the package when implementation is
authorized. The prior implementation was released as `1.0.5` in commit `6df3ef3`
with 147 passing tests and 2 pre-existing skips; that result does not verify the
new corrections described above. Keep version `1.0.5` unchanged as explicitly
requested. Implement and verify using offline tests only; do not write to a live
database or claim the external consuming translator has been fixed.

## Implemented Correction

The authorized follow-up now initializes confirmed missing, empty, or null
selected-proxy counters to `0` when writes are enabled and reads them back.
Existing numeric values are preserved. Initialization works in the base service
and at every verbose log level; failures remain explicitly local/unverified.
KeyVal missing-status and null responses have matching safe raw examples.
The requested run configuration and per-proxy detail categories are DEBUG-only.
Version remains `1.0.5`. Offline verification: 156 tests passed, with 2 existing
skips. No live database or external translator was modified.

The latest follow-up also makes both public counter getters initialize a
missing/null/empty value immediately, without requiring selection. Verification
and candidate filtering use the separate read-only method to prevent recursion
and avoid unused candidate records. Updated offline verification: 160 tests
passed, with 2 existing skips; the exact missing-response → SET 0 → GET sequence
is covered for both public getters. Version remains `1.0.5`.
