# 🧩 n_elastic_ip_pool

> Low-level Python service for managing an Elastic IP / IP pool and returning only validated, working proxy/IP resources.

## 🚀 Purpose

`n_elastic_ip_pool` is built using clean **N-layer architecture**.

Its goal is to separate business logic, storage access, external API calls, helpers, and constants into clear layers.

## ▶️ Usage

Install directly from GitHub:

```bash
pip install "git+https://github.com/R4Ajeti/n-elastic-ip-pool.git"
```

For test dependencies:

```bash
pip install "n-elastic-ip-pool[test] @ git+https://github.com/R4Ajeti/n-elastic-ip-pool.git"
```

Run the verbose Elastic IP pool service directly from Python:

```python
from core.service.verbose_elastic_ip_pool_service import VerboseElasticIpPoolService

verboseElasticIpPoolService = VerboseElasticIpPoolService()
verboseElasticIpPoolService.run()

print("Final selected proxy:", verboseElasticIpPoolService.finalValueStr)
print("Ranked proxy list:", verboseElasticIpPoolService.rankedProxyList)
```

## 🏗️ Architecture

```text
Controller / Entry Point
        ↓
     Service
     ↙     ↘
  Repo     Proxy
   ↓         ↓
Storage   External API
```

## 📁 Project Structure

```text
core/
  constant/   # Application constants
  helper/     # Generic reusable utilities
  proxy/      # External API abstraction layer
  service/    # Business logic
  repo/       # Data access layer

test/         # Unit tests matching core structure

raw/
  proxy/      # Safe request/input/output examples for proxy implementations

skill/        # Codex reusable project skills
```

## 🧠 Layer Responsibilities

| Layer | Responsibility |
|---|---|
| `service` | Business rules and orchestration |
| `repo` | Storage and data access abstraction |
| `proxy` | External API request abstraction |
| `helper` | Generic reusable utility logic |
| `constant` | Static application constants |

## 🔌 Proxy Rule

All external API calls must go through the `core/proxy/` layer.

Services must not call external APIs directly.

Each proxy implementation must include raw examples:

```text
raw/proxy/<proxy_name>/request.txt
raw/proxy/<proxy_name>/json/input.json
raw/proxy/<proxy_name>/json/output.json
```

## 🧪 Testing

Tests live outside `core/` and follow the same structure:

```text
test/
  constant/
  helper/
  proxy/
  service/
  repo/
```

Initial tests may be placeholders until implementation is completed.

Run the current test suite from the repository root:

```bash
python3 -m unittest discover -s test -p "test_*.py"
```

## 🔐 Safety

This project must never commit:

- `.env` files
- API keys
- cloud credentials
- proxy usernames/passwords
- private IPs
- tokens or session cookies
- sensitive provider data

## 🧭 First Milestone

Create only:

- project skeleton
- placeholder classes
- constants
- raw proxy examples
- placeholder tests

No real proxy validation or provider integration should be implemented in the first milestone.

## 🛠️ Built For

- Python
- Codex-assisted development
- Clean N-layer architecture
- External API abstraction
- Safe proxy/IP pool management
