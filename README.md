# n-elastic-ip-pool

`n-elastic-ip-pool` is a low-level Python package for discovering, validating,
ranking, caching, and returning working proxy/IP resources. It keeps provider
requests behind proxy classes, selection rules inside the service layer, and
storage access behind repository or KeyVal abstractions.

## Quick Start

Run the verbose service to check saved proxies, discover fresh candidates when
needed, validate them, and inspect the ranked result:

```python
from core.service.verbose_elastic_ip_pool_service import VerboseElasticIpPoolService

verboseElasticIpPoolService = VerboseElasticIpPoolService()
verboseElasticIpPoolService.run()

print("Final selected proxy:", verboseElasticIpPoolService.finalValueStr)
print("Ranked proxy list:", verboseElasticIpPoolService.rankedProxyList)
```

From this repository, the same flow is available through the example runner:

```bash
LOGGER=INFO python3 testKeyValueProxy.py
```

The runner also accepts optional parameters for more customizable discovery:

```bash
python3 testKeyValueProxy.py --release-channel beta --count 3 --selection-mode random --shuffle-candidates --random-seed 42
python3 testKeyValueProxy.py --release-channel stable --country US --proxy-type http --count 1
python3 testKeyValueProxy.py --release-channel canary --candidate-limit 500 --no-cache --no-save
```

Use `LOGGER=DEBUG` when you want to inspect ProxyScrape URLs, candidate rows,
validation attempts, KeyVal read and write URLs, and the final ranking.

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
- `search()` fetches proxy candidates from ProxyScrape, validates candidates,
  ranks working proxies, and saves a compact reusable list.
- `update(valueStr)` stores an explicit proxy value/list in KeyVal.
- Candidate proxy rows are normalized and deduplicated before validation.
- Working proxies must pass multiple validation checks before they are saved.
- Working proxies are ranked by average response timing, fastest first.
- KeyVal keys are hashed before storage.
- The verbose service exposes `finalValueStr` and `rankedProxyList` for manual
  runs and debugging.
- The codebase follows an N-layer structure: service, repo, proxy, helper, and
  constant.

## Basic Usage

```python
from core.service.elastic_ip_pool_service import ElasticIpPoolService

service = ElasticIpPoolService()

proxyStr = service.get()
print(proxyStr)
```

`get()` first tries cached KeyVal state through `check()`. If no saved proxy is
usable, it calls `search()` to discover and validate fresh candidates.

## Public API

Return the best currently available proxy:

```python
from core.service.elastic_ip_pool_service import ElasticIpPoolService

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
        +-- normalize and deduplicate rows
        +-- test each proxy against the target URL
        +-- require repeated successful validation
        +-- reject slow or failing proxies
        +-- rank working proxies by average timing
        +-- save a compact proxy list to KeyVal
```

By default, a proxy must pass three successful checks and stay within the
configured timing limit before it is considered usable.

## External Sources

The current provider abstractions are:

- `core/proxy/proxy_scrape_proxy.py` fetches candidate proxy rows from
  ProxyScrape.
- `core/proxy/elastic_ip_health_check_proxy.py` tests whether a candidate proxy
  can reach the configured target URL.
- `core/proxy/key_val_store_proxy.py` reads and writes saved proxy state through
  KeyVal.

External web calls are implemented only in `core/proxy/`. Services call those
proxy classes instead of calling provider URLs directly.

## Configuration

Runtime configuration can be passed through constructors when you need custom
providers, targets, timeouts, or validation thresholds:

```python
from core.proxy.elastic_ip_health_check_proxy import ElasticIpHealthCheckProxy
from core.proxy.key_val_store_proxy import KeyValStoreProxy
from core.proxy.proxy_scrape_proxy import ProxyScrapeProxy
from core.service.elastic_ip_pool_service import ElasticIpPoolService

service = ElasticIpPoolService(
    keyValStoreProxy=KeyValStoreProxy(baseUrlStr="https://api.keyval.org"),
    proxyScrapeProxy=ProxyScrapeProxy(countryFilterStr="all"),
    elasticIpHealthCheckProxy=ElasticIpHealthCheckProxy(
        targetUrlStr="https://api.ipify.org?format=json",
    ),
    proxyValidationSuccessCountInt=3,
    proxyMaxTimingMillisecondInt=2000,
)
```

The verbose runner uses these environment variables:

```bash
export LOGGER=INFO
export keyValStoreProxyStr="n-elastic-ip-pool-dummy-proxy-value"
```

`keyValStoreProxyStr` is a namespace/source string that is hashed before use as
the KeyVal storage key. Do not put secrets in public KeyVal values.

## Runner Options

`testKeyValueProxy.py` can be run with optional parameters when you want to make
candidate discovery and randomness more customizable:

| Option | Values | Default |
| --- | --- | --- |
| `--release-channel` | `stable`, `beta`, `canary` | `stable` |
| `--count` | integer, `0` means all that fit in KeyVal | channel default |
| `--selection-mode` | `fastest`, `random` | channel default |
| `--candidate-limit` | integer, `0` means all candidates | channel default |
| `--shuffle-candidates` / `--no-shuffle-candidates` | boolean flag | channel default |
| `--random-seed` | integer | unset |
| `--validation-count` | integer | channel default |
| `--max-timing-ms` | integer milliseconds | channel default |
| `--cache` / `--no-cache` | boolean flag | enabled |
| `--save` / `--no-save` | boolean flag | enabled |
| `--country` | `all`, `US`, or another ProxyScrape country filter | `all` |
| `--proxy-type` | `all`, `http`, `socks4`, `socks5` | `all` |
| `--ssl` | `yes`, `no`, or provider-supported value | `yes` |
| `--anonymity` | `elite`, `anonymous`, `transparent`, or provider-supported value | `elite` |
| `--target-url` | health-check URL | `https://api.ipify.org?format=json` |
| `--provider-base-url` | ProxyScrape-compatible base URL | `https://api.proxyscrape.com` |
| `--provider-timeout-ms` | ProxyScrape query timeout in milliseconds | `300` |
| `--provider-timeout-second` | network timeout for ProxyScrape and KeyVal | `10` |
| `--keyval-base-url` | KeyVal-compatible base URL | `https://api.keyval.org` |
| `--key-source` | string hashed into the KeyVal storage key | env/default key source |
| `--log-level` | `INFO`, `DEBUG` | `LOGGER` env or `INFO` |

Release channels are presets:

- `stable`: strict, predictable defaults. Uses fastest selection, no candidate
  shuffle, three validation passes, and a 2000 ms max health-check timing.
- `beta`: more exploratory. Keeps up to 3 proxies, shuffles candidates, uses
  random selection, validates 3 passes, and allows up to 2500 ms.
- `canary`: most exploratory. Keeps up to 5 proxies, shuffles candidates, uses
  random selection, validates 2 passes, limits candidates to 500, and allows up
  to 3500 ms.

CLI values override the release-channel preset. For repeatable random runs, pass
`--random-seed` with `--selection-mode random` or `--shuffle-candidates`.

## KeyVal Persistence

By default, KeyVal storage uses:

```text
https://api.keyval.org
```

Saved proxy values are intentionally compact because public KeyVal path writes
have small value limits. The service saves reusable proxy strings, not full
ranking metadata, and caps saved values before they exceed the configured
length.

## Logging

The verbose service supports two log levels:

```bash
LOGGER=INFO python3 testKeyValueProxy.py
LOGGER=DEBUG python3 testKeyValueProxy.py
```

`LOGGER=INFO` prints a compact discovery summary. `LOGGER=DEBUG` adds provider
URLs, candidate rows, validation results, cache URLs, and workflow details.

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
