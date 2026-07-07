# 010 - Geonode Free Proxy List Fallback Source

Follow `AGENTS.md` and the relevant repository skills before making changes:

- `skill/service-boundary-review/SKILL.md`
- `skill/proxy-example-contract/SKILL.md`

## Goal

Add Geonode Free Proxy List as a fallback proxy discovery source when the current ProxyScrape discovery source fails, returns an empty response, returns malformed data, or produces no usable working proxy after validation.

Do not replace the existing ProxyScrape flow. Keep ProxyScrape as the primary discovery source and use Geonode only as the fallback source.

## Background

The current implementation discovers proxy candidates through:

```text
core/proxy/proxy_scrape_proxy.py
```

Add a second provider abstraction for Geonode Free Proxy List:

```text
core/proxy/geonode_free_proxy_list_proxy.py
```

Use this public Geonode endpoint shape:

```text
https://proxylist.geonode.com/api/proxy-list
```

The free endpoint can return 500 records at a time with:

```text
https://proxylist.geonode.com/api/proxy-list?limit=500
```

The Geonode free proxy list returns JSON with a top-level `data` list. Each item may include fields such as:

```text
ip
port
protocols
country
anonymityLevel
latency
responseTime
upTime
lastChecked
updated_at
google
```

The proxy layer should map Geonode's provider-specific JSON into clean internal proxy candidate data. The service layer should not parse Geonode-specific response shapes directly.

## Default Geonode Query

Add typed constants and constructor defaults for the Geonode proxy:

```text
GEONODE_FREE_PROXY_LIST_API_BASE_URL_STR = "https://proxylist.geonode.com/api/proxy-list"
GEONODE_FREE_PROXY_LIST_LIMIT_INT = 500
GEONODE_FREE_PROXY_LIST_PAGE_INT = 1
GEONODE_FREE_PROXY_LIST_SORT_BY_STR = "lastChecked"
GEONODE_FREE_PROXY_LIST_SORT_TYPE_STR = "desc"
GEONODE_FREE_PROXY_LIST_PROTOCOLS_STR = "http,https"
GEONODE_FREE_PROXY_LIST_ANONYMITY_LEVEL_STR = "elite"
GEONODE_FREE_PROXY_LIST_MIN_UPTIME_INT = 80
```

Use URL query parameters similar to:

```text
limit=500
page=1
sort_by=lastChecked
sort_type=desc
protocols=http,https
anonymityLevel=elite
filterUpTime=80
```

Before finalizing the implementation, verify the current Geonode endpoint parameter names from the live free proxy list page or endpoint behavior. If a parameter is no longer accepted, keep the constant but document the adjusted request behavior in the proxy raw example.

## Required Flow

Update the proxy discovery flow so it behaves like this:

1. `get()` still checks saved proxies first when saved proxies are enabled.
2. If no saved proxy is usable, call `search()`.
3. `search()` should try ProxyScrape first.
4. If ProxyScrape fails, returns an empty candidate list, returns malformed data, or every ProxyScrape candidate fails validation, try Geonode.
5. Parse and normalize Geonode candidates through `GeonodeFreeProxyListProxy`.
6. Reuse the existing service validation, timing, ranking, usage-history, and optional KeyVal persistence behavior.
7. Return the fastest validated working proxy.
8. Return `None` only when both provider sources fail or produce no validated working proxy.

Do not call Geonode directly from the service with raw HTTP code. All external Geonode API calls must live inside `core/proxy/geonode_free_proxy_list_proxy.py`.

## Geonode Proxy Class

Create:

```text
core/proxy/geonode_free_proxy_list_proxy.py
```

Suggested class names:

```text
GeonodeFreeProxyListProxy
GeonodeFreeProxyListProxyError
```

The proxy should:

- Build the Geonode request URL from constructor values.
- Use `GET`.
- Send safe headers, including `Accept: application/json` and the existing user agent constant.
- Handle HTTP errors, timeouts, URL errors, malformed JSON, and missing fields.
- Return normalized data that the service can consume.
- Avoid business rules such as deciding final proxy usability.

Suggested proxy methods:

```text
buildFetchUrl()
fetchProxyCandidateText()
parseProxyCandidateJson()
normalizeProxyRecord()
```

To minimize service churn, `fetchProxyCandidateText()` may return newline-delimited `host:port` values under the existing response key:

```text
{
  "url": "...",
  "status_code": 200,
  "proxy_candidate_text": "proxy-one.example.net:8080\nproxy-two.example.net:3128\n"
}
```

If useful, include provider metadata in an additional key such as `proxy_candidate_metadata_list`, but do not make the service depend on provider-specific fields unless there is a clear reason.

## Protocol Handling

Start with HTTP and HTTPS candidates only unless the existing health-check proxy already supports SOCKS protocols.

If Geonode returns `socks4` or `socks5` records and the current health-check proxy cannot validate them safely, skip those records in the Geonode proxy normalization step or make the allowed protocols configurable with HTTP/HTTPS defaults.

Do not add SOCKS support unless it is covered by deterministic tests and does not require live providers.

## Fallback Design

Keep the fallback implementation simple and explicit. Do not create a generic provider framework or base proxy class unless the existing codebase already has that pattern.

Suggested service shape:

```text
search()
searchProviderProxyCandidateList(sourceNameStr, candidateTextStr)
fetchProxyScrapeCandidateText()
fetchGeonodeFreeProxyCandidateText()
```

Use project style and existing method names where possible.

Track which provider produced the selected proxy in usage metadata:

```text
source: "proxyscrape_discovered_proxy"
source: "geonode_free_proxy_discovered_proxy"
```

If the existing usage metadata shape already uses another source string, adapt these names to match the project style.

## Raw Proxy Examples

Because this adds a new proxy implementation, also add the required raw example contract files:

```text
raw/proxy/geonode_free_proxy_list_proxy/request.txt
raw/proxy/geonode_free_proxy_list_proxy/json/input.json
raw/proxy/geonode_free_proxy_list_proxy/json/output.json
```

`request.txt` should include:

- Geonode endpoint URL.
- HTTP method.
- Query parameters.
- Required headers.
- A short explanation that this fetches public free proxy candidates.
- A warning that public free proxies are only for testing or non-sensitive traffic.
- Authentication notes: no credentials are required for the free endpoint.

`json/input.json` should include safe example configuration, such as:

```json
{
  "baseUrl": "https://proxylist.geonode.com/api/proxy-list",
  "limit": 500,
  "page": 1,
  "sortBy": "lastChecked",
  "sortType": "desc",
  "protocols": "http,https",
  "anonymityLevel": "elite",
  "filterUpTime": 80
}
```

`json/output.json` should show a safe normalized output shape using example hostnames or reserved documentation IP ranges only. Do not include real public proxy IPs copied from Geonode.

Example:

```json
{
  "url": "https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&sort_by=lastChecked&sort_type=desc&protocols=http%2Chttps&anonymityLevel=elite&filterUpTime=80",
  "status_code": 200,
  "proxy_candidate_text": "proxy-one.example.net:8080\nproxy-two.example.net:3128\n",
  "proxy_candidate_metadata_list": [
    {
      "proxy": "proxy-one.example.net:8080",
      "protocols": ["http"],
      "country": "US",
      "anonymityLevel": "elite",
      "upTime": 98.5,
      "latency": 120.5,
      "responseTime": 350
    }
  ]
}
```

## Tests

Add or update mocked unit tests only. Tests must not call the real Geonode API, ProxyScrape API, KeyVal API, Firebase, or real proxy endpoints.

Cover at least:

1. `GeonodeFreeProxyListProxy.buildFetchUrl()` builds the expected default URL.
2. Geonode query parameters can be overridden.
3. Geonode JSON records are normalized into newline-delimited `host:port` candidate text.
4. Geonode records missing `ip` or `port` are skipped.
5. Geonode records with unsupported protocols are skipped when only HTTP/HTTPS are enabled.
6. Malformed Geonode JSON raises or returns a project-consistent provider error.
7. Geonode HTTP errors are wrapped in `GeonodeFreeProxyListProxyError`.
8. Service does not call Geonode when ProxyScrape returns usable working proxies.
9. Service calls Geonode when ProxyScrape fetch fails.
10. Service calls Geonode when ProxyScrape returns empty or malformed candidate data.
11. Service calls Geonode when ProxyScrape candidates all fail validation.
12. Service returns the fastest validated Geonode proxy when fallback succeeds.
13. Service returns `None` when both ProxyScrape and Geonode fail.
14. Working Geonode fallback proxies are saved only when existing save configuration allows it.
15. Usage history records the fallback source when a Geonode proxy is selected.
16. No tests require live internet access or real provider credentials.

Suggested files:

```text
core/constant/elastic_ip_pool_constant.py
core/proxy/geonode_free_proxy_list_proxy.py
core/service/elastic_ip_pool_service.py
test/constant/test_elastic_ip_pool_constant.py
test/proxy/test_geonode_free_proxy_list_proxy.py
test/service/test_elastic_ip_pool_service.py
raw/proxy/geonode_free_proxy_list_proxy/request.txt
raw/proxy/geonode_free_proxy_list_proxy/json/input.json
raw/proxy/geonode_free_proxy_list_proxy/json/output.json
```

Run:

```bash
python3 -m unittest discover -s test -p "test_*.py"
```

## Safety Rules

Do not commit:

- real Geonode proxy IPs copied from live responses
- real proxy credentials
- usernames or passwords
- tokens
- session cookies
- provider secrets
- cloud credentials
- `.env` files
- private IPs
- production request dumps

Use safe examples only:

```text
proxy-one.example.net:8080
proxy-two.example.net:3128
203.0.113.10:8080
198.51.100.20:3128
```

Public free proxies can be unstable and unsafe. The implementation should treat Geonode Free Proxy List as a fallback discovery source for testing or non-sensitive traffic, not as a trusted channel for credentials, customer data, or private infrastructure access.

## Completion Checklist

Before finishing:

- Verify N-layer structure is respected.
- Verify ProxyScrape remains the primary provider.
- Verify Geonode is called only as fallback.
- Verify all Geonode HTTP logic lives in `core/proxy/`.
- Verify the service owns fallback, validation, selection, ranking, and persistence decisions.
- Verify the proxy layer only fetches and normalizes provider data.
- Verify constants use UPPER_SNAKE_CASE with type suffixes.
- Verify all modified or new proxy classes include matching raw examples.
- Verify raw example JSON files are valid JSON.
- Verify tests use mocks and do not make live network calls.
- Verify no secrets or real proxy credentials are committed.
