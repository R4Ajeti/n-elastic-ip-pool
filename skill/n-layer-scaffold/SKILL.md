---
name: n-layer-scaffold
description: Use this when creating or updating the initial N-layer project structure for n_elastic_ip_pool.
---

# N-Layer Scaffold Skill

## Goal

Create or update the project structure using the approved N-layer architecture.

## Required Structure

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
```

## Rules

- Use singular naming everywhere.
- Create `__init__.py` files where needed.
- Create placeholder files only during the scaffold phase.
- Do not implement real proxy validation logic.
- Do not add external service calls.
- Do not add cloud provider integrations.
- Do not add credentials or config secrets.

## Expected Placeholder Files

```text
core/constant/elastic_ip_pool_constant.py
core/helper/ip_address_format_helper.py
core/proxy/elastic_ip_health_check_proxy.py
core/proxy/key_val_store_proxy.py
core/service/elastic_ip_pool_service.py
core/repo/elastic_ip_pool_repo.py
```

## Expected Placeholder Test Files

```text
test/constant/test_elastic_ip_pool_constant.py
test/helper/test_ip_address_format_helper.py
test/proxy/test_elastic_ip_health_check_proxy.py
test/proxy/test_key_val_store_proxy.py
test/service/test_elastic_ip_pool_service.py
test/repo/test_elastic_ip_pool_repo.py
```

## Expected Raw Proxy Example Files

```text
raw/proxy/elastic_ip_health_check_proxy/request.txt
raw/proxy/elastic_ip_health_check_proxy/json/input.json
raw/proxy/elastic_ip_health_check_proxy/json/output.json
raw/proxy/key_val_store_proxy/request.txt
raw/proxy/key_val_store_proxy/json/input.json
raw/proxy/key_val_store_proxy/json/output.json
```

## Output Requirement

After changes, show the final file tree and summarize what was created.
