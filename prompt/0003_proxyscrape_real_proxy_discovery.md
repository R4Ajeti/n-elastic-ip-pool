# 005 - ProxyScrape Real Proxy Discovery

Please update the current proxy-management implementation from using only dummy proxies to searching, validating, ranking, and storing real proxies from ProxyScrape.

Act as a senior software engineering team lead with strong experience in backend systems, proxy infrastructure, elastic IP management, socket programming, HTTP networking, and scalable network services.

The goal is to keep the implementation clean, maintainable, testable, and production-ready while still being simple enough for the current project.

## Context

The current service uses a dummy proxy and saves a hashed value to KeyVal.

Now we need to replace the dummy-only behavior with a real proxy discovery flow using this ProxyScrape API:

```text
https://api.proxyscrape.com/?request=getproxies&proxytype=all&timeout=300&country=all&ssl=yes&anonymity=elite
```

This URL and its query parameters should be configurable.

Add the ProxyScrape settings as optional/default parameters, with the current values used as defaults:

- `request=getproxies`
- `proxytype=all`
- `timeout=300`
- `country=all`
- `ssl=yes`
- `anonymity=elite`

Do not hardcode the full URL deep inside business logic. Use descriptive constants, configuration values, or constructor defaults where appropriate.

## Required Flow

Update the `get()` method so it behaves like this:

1. Build or resolve the expected proxy key.
2. Hash the proxy key using the existing string-hashing helper.
3. Check KeyVal for an existing value using that hashed key.
4. If a saved value exists:
   - Read it.
   - Parse it as one or more saved proxies.
   - Test the saved proxies.
   - If at least one saved proxy is still working, return the best working proxy.
5. If no saved proxy exists, or all saved proxies fail:
   - Call a new internal/public method named `search()`.
   - `search()` should fetch proxies from the ProxyScrape API.
   - Parse the returned proxy list safely.
   - Test each candidate proxy once.
   - Keep only proxies that pass the first test.
   - Test the passing proxies again until a proxy has passed 3 successful checks total.
   - Only proxies that pass 3 times should be considered working.
   - Measure response timing for every successful proxy test.
   - Sort working proxies by timing ascending, fastest first.
   - Save the working proxies to KeyVal under the hashed key.
   - Return the fastest working proxy.

## Proxy Testing Requirements

Implement proxy testing in a dedicated method, for example:

```text
testProxy(proxy)
```

or follow the project’s existing naming convention.

The proxy test should:

- Use a safe external target endpoint for testing connectivity.
- Support reasonable timeout handling.
- Fail gracefully on connection errors, DNS errors, invalid proxy format, timeout, SSL errors, and unexpected response codes.
- Return structured information, not only true/false.

Suggested result shape:

```text
{
  proxy: "...",
  isWorking: true,
  timingMs: 123,
  checkedAt: "...",
  error: null
}
```

Use the existing project style and language conventions.

## Ranking Logic

After collecting candidate proxies from ProxyScrape:

1. Remove duplicates.
2. Ignore empty or malformed rows.
3. Test every proxy once.
4. Keep only first-pass working proxies.
5. Retest those candidates until they reach 3 successful checks total.
6. Discard proxies that fail during retesting.
7. Sort final working proxies by average timing ascending.
8. Save the sorted list.
9. Return the fastest one.

The saved value should contain enough information to reuse later, for example:

```text
[
  {
    "proxy": "host:port",
    "averageTimingMs": 120,
    "successCount": 3,
    "lastCheckedAt": "..."
  }
]
```

Hash sensitive proxy values before saving if that is required by the current architecture, but be careful: if the app needs to reuse the proxy later, it must still be able to retrieve the usable proxy value. If hashing prevents reuse, store metadata safely and document the tradeoff clearly in code comments or tests.

## Architecture Expectations

Keep responsibilities separated:

- KeyVal integration should stay inside its own service/module.
- ProxyScrape fetching should be isolated from proxy testing.
- Proxy validation/ranking should be isolated from persistence.
- Constants/configuration should not be scattered across the codebase.
- The public API of the service should remain simple, ideally `get()`.
- `get()` should orchestrate the flow, not contain all low-level logic.

Suggested methods:

```text
get()
check()
search()
update()
fetchProxyCandidates()
parseProxyCandidates()
testProxy()
rankWorkingProxies()
saveWorkingProxies()
```

Use only the methods that make sense for the existing codebase. Do not over-engineer, but keep the design easy to extend later.

## Error Handling

Handle these cases carefully:

- ProxyScrape API is down.
- ProxyScrape returns an empty response.
- ProxyScrape returns malformed data.
- KeyVal API is down.
- Saved KeyVal data is corrupted or not valid JSON.
- Saved proxies exist but none are working.
- Proxy test endpoint is down.
- All proxies fail validation.
- Network timeout happens during testing.
- Duplicate proxies are returned.
- Proxy contains invalid host or port.
- SSL proxy fails HTTPS test.
- Proxy is slow but technically working.
- Partial success: some proxies fail, some pass.
- Saving to KeyVal fails after working proxies were found.

When a failure happens, return a clear and safe result or raise a project-consistent exception. Do not silently swallow important failures unless the project already follows that pattern.

## Tests

Add or update tests for the new behavior.

Cover at least these cases:

1. `get()` returns a saved working proxy from KeyVal.
2. `get()` ignores saved proxies that fail validation.
3. `get()` calls `search()` when KeyVal has no saved proxy.
4. `search()` fetches proxies from ProxyScrape.
5. ProxyScrape query parameters use defaults correctly.
6. ProxyScrape query parameters can be overridden.
7. Duplicate proxies are removed.
8. Malformed proxy rows are ignored.
9. Proxies are tested once before retesting.
10. Only proxies with 3 successful checks are saved.
11. Working proxies are sorted by average timing ascending.
12. The fastest proxy is returned first.
13. Empty ProxyScrape response is handled safely.
14. ProxyScrape API failure is handled safely.
15. Corrupted KeyVal data is handled safely.
16. KeyVal save failure is handled safely.
17. Timeout during proxy testing is handled safely.
18. No real secrets, credentials, tokens, sponsor codes, `.env` values, or real private proxy credentials are committed.

Use mocks for external APIs. Tests should not depend on the real ProxyScrape API or real KeyVal service.

## Production Readiness

Please also review the implementation for:

- clear naming
- clean separation of concerns
- project-style consistency
- no unnecessary abstractions
- safe logging
- no sensitive data leaks
- reasonable timeouts
- deterministic tests
- easy future replacement of ProxyScrape with another provider

Surprise me by adding useful edge-case handling, clean helper methods, or small reliability improvements that make the implementation feel production-ready without making it overly complex.

Important: Do not make real network calls in tests. Mock ProxyScrape, KeyVal, and proxy validation.
