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
core/constant/base_proxy_constant.py
core/helper/proxy_format_helper.py
core/proxy/proxy_client.py
core/service/proxy_service.py
core/repo/proxy_repo.py
```

## Expected Placeholder Test Files

```text
test/constant/test_base_proxy_constant.py
test/helper/test_proxy_format_helper.py
test/proxy/test_proxy_client.py
test/service/test_proxy_service.py
test/repo/test_proxy_repo.py
```

## Output Requirement

After changes, show the final file tree and summarize what was created.
