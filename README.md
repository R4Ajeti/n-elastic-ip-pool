# n-elastic-ip-pool

`n-elastic-ip-pool` (version `1.0.2`) is a low-level Python package for discovering, validating,
ranking, caching, and returning working proxy/IP resources. It keeps provider
requests behind proxy classes, selection rules inside the service layer, and
storage access behind repository or KeyVal abstractions.

## Quick Start

Run a deterministic local flow with injected fake providers:

```python
from n_elastic_ip_pool.service.elastic_ip_pool_service import ElasticIpPoolService


class FakeProxyScrapeProxy:
    def fetchProxyCandidateText(self) -> dict:
        return {
            "status_code": 200,
            "proxy_candidate_text": "proxy-one.example.net:8080\n",
        }


class FakeElasticIpHealthCheckProxy:
    def testProxy(self, proxyStr: str) -> dict:
        return {
            "proxy": proxyStr,
            "isWorking": True,
            "timingMs": 50,
            "checkedAt": "2026-01-01T00:00:00Z",
            "error": None,
            "statusCode": 200,
        }


service = ElasticIpPoolService(
    proxyScrapeProxy=FakeProxyScrapeProxy(),
    elasticIpHealthCheckProxy=FakeElasticIpHealthCheckProxy(),
    proxyValidationSuccessCountInt=1,
    useSavedProxyBool=False,
    saveWorkingProxyBool=False,
)

proxyStr = service.get()

print(proxyStr)
print(service.rankedProxyList)
```

This example does not call the internet and does not write to public KeyVal
storage.

## Installation

Install from GitHub:

```bash
pip install "git+https://github.com/R4Ajeti/n-elastic-ip-pool.git"
```

Install with test dependencies:

```bash
pip install "n-elastic-ip-pool[test] @ git+https://github.com/R4Ajeti/n-elastic-ip-pool.git"
```

Install locally for development:

```bash
pip install -e ".[test]"
```

The package requires Python 3.11 or newer and has no required third-party
runtime dependencies.

## Purpose

This project is designed for legitimate proxy/IP health checking,
infrastructure-safe resource validation, reusable service logic, and clean
external API abstraction.

It does not provide scraping evasion, CAPTCHA bypass, rate-limit bypass,
credential stuffing, account abuse, spam automation, stealth workflow logic, or
restriction bypass behavior.

## Features

- `get()` returns a usable proxy string or `None`.
- `check()` reads saved proxy values from KeyVal and revalidates them before
  use.
- `search()` fetches proxy candidates, validates candidates, and ranks working
  proxies. ProxyScrape is tried first, with Geonode Free Proxy List used only
  as a fallback.
- `update(valueStr)` stores an explicit proxy value/list in KeyVal.
- Candidate proxy rows are normalized and deduplicated before validation.
- Newly discovered proxies must pass the configured validation checks before
  they are returned or optionally saved. Cached proxies must pass one fresh check.
- Working proxies are ranked by average response timing, fastest first.
- KeyVal keys are hashed before storage.
- The verbose service exposes `finalValueStr` and `rankedProxyList` for manual
  runs and debugging.
- The codebase follows an N-layer structure: service, repo, proxy, helper, and
  constant.

## Basic Usage

```python
from n_elastic_ip_pool.service.elastic_ip_pool_service import ElasticIpPoolService

service = ElasticIpPoolService()

proxyStr = service.get()
print(proxyStr)
```

`get()` first tries cached KeyVal state through `check()`. If no saved proxy is
usable, it calls `search()` to discover and validate fresh candidates. Working
proxy lists are saved to KeyVal by default.

Every eligible cached proxy is checked once during the current lookup. Only
proxies that pass that check within the configured timing limit appear in
`rankedProxyList` and `rankedProxyDictList`; a working entry does not make the
rest of the cache usable. `get()` and `check()` return one selected working proxy,
not the cached list. Previous ranked results are cleared on each lookup, leaving
empty lists if no proxies pass and returning `None` when none are available.

## Public API

Return the best currently available proxy:

```python
from n_elastic_ip_pool.service.elastic_ip_pool_service import ElasticIpPoolService

service = ElasticIpPoolService()

proxyStr = service.get()
```

Check only the saved KeyVal proxy list:

```python
cachedProxyStr = service.check()
```

Discover and validate new candidates:

```python
freshProxyStr = service.search()
```

Store an explicit proxy list value:

```python
service = ElasticIpPoolService(keyValStoreProxyStr="my-local-demo-key-source")
service.update('["proxy-one.example.net:8080","proxy-two.example.net:8080"]')
```

After `get()`, `check()`, or `search()`, inspect the ranked proxy list:

```python
print(service.rankedProxyList)
print(service.rankedProxyDictList)
```

## Validation Flow

The service uses this flow:

```text
get()
  |
  +-- check() saved KeyVal values
  |     |
  |     +-- revalidate saved proxies
  |
  +-- search() when cache is empty or unusable
        |
        +-- fetch ProxyScrape candidate text
        +-- fetch Geonode Free Proxy List candidate text only if needed
        +-- normalize and deduplicate rows
        +-- test each proxy against the target URL
        +-- require repeated successful validation
        +-- reject slow or failing proxies
        +-- rank working proxies by average timing
        +-- optionally save a compact proxy list to KeyVal
```

By default, a proxy must pass three successful checks and stay within the
configured timing limit before it is considered usable.

## External Sources

The current provider abstractions are:

- `core/proxy/proxy_scrape_proxy.py` fetches candidate proxy rows from
  ProxyScrape.
- `core/proxy/geonode_free_proxy_list_proxy.py` fetches fallback candidate
  proxy rows from Geonode Free Proxy List.
- `core/proxy/elastic_ip_health_check_proxy.py` tests whether a candidate proxy
  can reach the configured target URL.
- `core/proxy/key_val_store_proxy.py` reads and writes saved proxy state through
  KeyVal.

External web calls are implemented only in `core/proxy/` and are packaged under
`n_elastic_ip_pool.proxy`. Services call those proxy classes instead of calling
provider URLs directly.

## Configuration

Runtime configuration can be passed through constructors when you need custom
providers, targets, timeouts, or validation thresholds:

```python
from n_elastic_ip_pool.proxy.elastic_ip_health_check_proxy import ElasticIpHealthCheckProxy
from n_elastic_ip_pool.proxy.key_val_store_proxy import KeyValStoreProxy
from n_elastic_ip_pool.proxy.proxy_scrape_proxy import ProxyScrapeProxy
from n_elastic_ip_pool.service.elastic_ip_pool_service import ElasticIpPoolService

service = ElasticIpPoolService(
    keyValStoreProxy=KeyValStoreProxy(baseUrlStr="https://api.keyval.org"),
    proxyScrapeProxy=ProxyScrapeProxy(countryFilterStr="all"),
    elasticIpHealthCheckProxy=ElasticIpHealthCheckProxy(
        targetUrlStr="https://api.ipify.org?format=json",
    ),
    proxyValidationSuccessCountInt=3,
    proxyMaxTimingMillisecondInt=2000,
    saveWorkingProxyBool=False,
)
```

The app supports these environment variables:

```bash
export DEBUGGING=true
export LOGGER=INFO
export keyValStoreProxyStr="my-local-demo-key-source"
export KEY_VAL_BASE_URL="https://api.keyval.org"
export KEY_VAL_AUTH_TOKEN=""
export PROXY_TEST_TARGET_URL="https://api.ipify.org?format=json"
export PROXY_MAX_TIMING_MILLISECOND=2000
```

`DEBUGGING=true` selects `DEBUG`, while `DEBUGGING=false` selects `INFO`.
When both logging variables are nonblank, `DEBUGGING` takes precedence over
`LOGGER`. If `DEBUGGING` is unset or blank, `LOGGER` controls the level.

`keyValStoreProxyStr` is a namespace/source string that is hashed before use as
the KeyVal storage key. Do not put secrets in public KeyVal values.

`KEY_VAL_BASE_URL` enables external KeyVal-compatible cache reads and writes.
Leave it blank to keep the run local. `KEY_VAL_AUTH_TOKEN` is optional and is
sent as a bearer token only when a private compatible provider requires it.
`PROXY_TEST_TARGET_URL` is the endpoint every candidate must reach, and
`PROXY_MAX_TIMING_MILLISECOND` controls both the health-check timeout and the
maximum accepted response time.

## Live Provider Demo

From a repository checkout, the live provider flow is available through the
app entry point:

```bash
DEBUGGING=true LOGGER=info python3 app/key_value_proxy_app.py
```

The app uses ProxyScrape and the configured health-check URL. KeyVal cache reads
and writes are enabled by default. When `KEY_VAL_BASE_URL` is blank, the default
KeyVal endpoint is used. Set `keyValStoreProxyStr` in `.env` to use a separate
cache namespace.

Live runs are network-dependent and can fail because of provider availability,
provider limits, target availability, or candidate proxy quality.

## KeyVal Persistence

To enable the public KeyVal provider, configure:

```text
KEY_VAL_BASE_URL=https://api.keyval.org
```

Saved proxy values are intentionally compact because public KeyVal path writes
have small value limits. The service saves reusable proxy strings, not full
ranking metadata, and caps saved values before they exceed the configured
length. The app uses the default KeyVal endpoint when `KEY_VAL_BASE_URL` is
blank. Pass `useSavedProxyBool=False` to skip cache reads or
`saveWorkingProxyBool=False` for a read-only service instance. Set
`keyValStoreProxyStr` to use a separate cache namespace.

## Logging

The verbose service supports two log levels:

```bash
DEBUGGING=false python3 app/key_value_proxy_app.py
DEBUGGING=true python3 app/key_value_proxy_app.py
LOGGER=INFO python3 app/key_value_proxy_app.py
LOGGER=DEBUG python3 app/key_value_proxy_app.py
```

`DEBUGGING=false` or `LOGGER=INFO` prints a compact discovery summary with
proxy values redacted. `DEBUGGING=true` or `LOGGER=DEBUG` adds provider URLs,
candidate rows, validation results, cache URL shapes, and workflow details
while redacting proxy values and KeyVal paths.

## Architecture

The repository follows N-layer architecture:

```text
Controller or Entry Point
        |
        v
     Service
     /     \
    v       v
  Repo    Proxy
    |       |
    v       v
 Storage  External API
```

Layer responsibilities:

| Layer | Responsibility |
| --- | --- |
| `service` | Business rules and orchestration |
| `repo` | Local or future persistent data access |
| `proxy` | External API request and response abstraction |
| `helper` | Generic reusable utility functions |
| `constant` | Application constants only |

Current structure:

```text
core/
  constant/
  helper/
  proxy/
  service/
  repo/

test/
  constant/
  helper/
  proxy/
  service/
  repo/

raw/
  proxy/

skill/
```

## Proxy Contract

All external web API calls must go through `core/proxy/`.

Each proxy implementation has matching safe raw examples:

```text
raw/proxy/<proxy_name>/request.txt
raw/proxy/<proxy_name>/json/input.json
raw/proxy/<proxy_name>/json/output.json
```

The raw examples document request shape and expected payloads without storing
credentials, tokens, private infrastructure details, private IPs, or production
request dumps.

## Testing

Run the unit test suite from the repository root:

```bash
python3 -m unittest discover -s test -p "test_*.py"
```

Or run the pytest suite when installed with the test extra:

```bash
pytest
```

Tests use fakes and local fixtures for service behavior. They do not require
real proxy providers, real cloud credentials, paid services, private
infrastructure, or live Elastic IP ownership.

## Development Notes

When contributing, keep these project rules intact:

- Use singular folder and file naming.
- Keep service, repo, proxy, helper, and constant responsibilities separated.
- Put external API behavior in proxy classes only.
- Keep proxy selection and validation rules in the service layer.
- Update matching `raw/proxy/` examples whenever a proxy contract changes.
- Do not commit `.env` files, credentials, tokens, cookies, private keys,
  private IPs, or production request dumps.

## License

MIT
