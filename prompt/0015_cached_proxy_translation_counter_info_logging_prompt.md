# 015 - Show Cached Proxy Counter Key and Value at INFO

Follow AGENTS.md and the service-boundary-review skill. Save this prompt before
implementation changes.

User clarification: make logging professional and clean. Keep INFO summaries
short and consistently labeled; put advanced run options and repetitive setup
notes at DEBUG. Use one counter-line formatter for reads and writes.
Also show the proxy-cache variable name, actual hashed KeyVal cache key, and
credential-redacted saved proxy value at INFO, alongside the selected proxy.
Keep proxy-cache entries distinct from translation-counter entries.
Prefix every package log line with `[n-elastic-ip-pool] [INFO]` or
`[n-elastic-ip-pool] [DEBUG]`. Preserve category markers for filtering. Route all
output through the shared formatter, including multiline values; remove duplicate
unprefixed entry-point result prints.

The run options line is configuration, not the KeyVal translation counter.
Log the exact selected proxy counter key and count even when the run uses a
cached proxy and no reset/translation update takes place. Preserve all counters.

Distinguish actual KeyVal values, missing keys (effective zero), local-only
values, and fallback values after a failed read. Do not present local values as
verified database values. Do not log credentials, unhashed namespaces, or full
URLs. Retain the searchable `[translation-count]` marker.

Label the historical usage limit separately from translation upper/lower
limits in the options line. Explain when no proxy is selected. Add offline tests
for cached run/get/check logging, stored and missing keys, failed reads, and quiet
log levels. Update README, bump to 1.0.5, verify, commit, and push the correction.
