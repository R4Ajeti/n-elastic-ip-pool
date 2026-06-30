# AGENTS.md

## Project

Project name: `n_elastic_ip_pool`

This is a low-level Python project for managing an Elastic IP / IP pool system and returning only validated, working proxy/IP resources.

The project must follow clean N-layer programming principles and keep responsibilities separated between service, repo, proxy, helper, and constant layers.

## Codex Instructions

Before making changes, read this file and follow the relevant skill from the `skill/` directory.

Use repository skills for repeatable workflows:

- `skill/n-layer-scaffold/SKILL.md`
- `skill/service-boundary-review/SKILL.md`
- `skill/test-placeholder/SKILL.md`
- `skill/proxy-example-contract/SKILL.md`

If Codex native skill discovery is available, use the `.agents/skills` symlink, which points to `skill/`.

## Architecture

Use N-layer programming.

Required flow:

```text
Controller or Entry Point → Service → Repo → Storage
Controller or Entry Point → Service → Proxy → External API
```

The service layer coordinates application logic.

The repo layer abstracts storage/data access.

The proxy layer abstracts external API calls.

The helper layer contains generic reusable utility functions only.

The constant layer contains application constants only.

Required folders:

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
```

## Naming Rules

Use singular naming everywhere.

Use snake_case for folders and files.

Use PascalCase for classes.

Use camelCase for Python functions and methods.

Use UPPER_SNAKE_CASE for constants.

All constants must include a type suffix.

Examples:

- `CORE_LOGGER_NAME_STR`
- `DEFAULT_TIMEOUT_SECOND_INT`
- `MAX_ELASTIC_IP_FAILURE_COUNT_INT`
- `ELASTIC_IP_HEALTH_CHECK_URL_STR`
- `DEFAULT_PROXY_COUNTRY_CODE_STR`

Avoid generic file names when a descriptive domain name is possible.

Good examples:

- `elastic_ip_pool_service.py`
- `elastic_ip_pool_repo.py`
- `elastic_ip_health_check_proxy.py`
- `ip_address_format_helper.py`
- `elastic_ip_pool_constant.py`
- `key_val_store_proxy.py`

Bad examples:

- `proxy_service.py`
- `proxy_repo.py`
- `proxy_client.py`
- `base_proxy.py`
- `api_proxy.py`
- `helper.py`
- `constant.py`

## Layer Rules

### constant

The `constant` folder contains only application constants.

Rules:

- Store constants only.
- Do not store business logic.
- Do not store runtime calculations.
- Use descriptive names.
- Use UPPER_SNAKE_CASE.
- Add a type suffix to every constant.
- Split constants into subfolders when a file becomes too large or mixes multiple domains.

Example:

```text
core/constant/elastic_ip_pool_constant.py
```

### helper

The `helper` folder contains only generic reusable utility functions.

Rules:

- Helpers must be safe to reuse outside the project.
- Helpers must not contain business logic.
- Helpers must not contain provider-specific logic.
- Helpers must not contain credentials or sensitive implementation details.
- Helpers should solve small generic problems such as formatting, parsing, validation, or simple calculations.

Example:

```text
core/helper/ip_address_format_helper.py
```

### proxy

The `proxy` folder contains external API abstraction classes.

In this architecture, a proxy is not the same thing as a network proxy.

A proxy is responsible for calling external systems, providers, HTTP APIs, SDKs, or cloud services and converting their responses into clean internal data.

Services must not call external APIs directly. Services should call proxy classes.

Required flow:

```text
Service → Proxy → External API
```

Rules:

- Proxy classes make external API calls.
- Proxy classes abstract external providers from services.
- Proxy classes handle request construction.
- Proxy classes handle response parsing/mapping.
- Proxy classes handle provider-specific errors.
- Proxy classes must not contain business rules.
- Proxy classes must not contain storage/database logic.
- Proxy classes must not expose credentials or raw provider secrets.
- Proxy classes must not decide which IP/proxy resource should be selected for business use.

Example:

```text
core/proxy/elastic_ip_health_check_proxy.py
```

Good proxy names:

- `elastic_ip_health_check_proxy.py`
- `public_ip_lookup_proxy.py`
- `aws_elastic_ip_proxy.py`
- `key_val_store_proxy.py`
- `proxy_provider_status_proxy.py`
- `geo_ip_lookup_proxy.py`

Bad proxy names:

- `proxy_client.py`
- `base_proxy.py`
- `api_proxy.py`
- `some_thing_proxy.py`

Whenever a proxy class is implemented or modified, follow:

- `skill/proxy-example-contract/SKILL.md`

Every proxy implementation must include matching raw examples:

```text
raw/proxy/<proxy_name>/request.txt
raw/proxy/<proxy_name>/json/input.json
raw/proxy/<proxy_name>/json/output.json
```

A proxy implementation is not complete unless these files are added or updated.

### service

The `service` folder contains business logic.

Rules:

- Services coordinate repos, proxies, helpers, and constants.
- Services contain business rules.
- Services decide which Elastic IP/proxy resource is usable.
- Services decide when to retry.
- Services decide when to mark a resource as failed.
- Services decide when to return no available resource.
- Services must not contain raw database/storage logic.
- Services must not call external APIs directly.
- Services must call proxy classes for external API communication.
- Services must call repo classes for data access.

Example:

```text
core/service/elastic_ip_pool_service.py
```

### repo

The `repo` folder contains data access logic.

Rules:

- Repos hide storage details from services.
- Repos handle create/read/update/delete operations.
- Repos do not contain business rules.
- Repos do not call external APIs directly.
- Repos do not decide which Elastic IP/proxy resource is usable.
- The first version may use placeholder or in-memory repo methods only.

Example:

```text
core/repo/elastic_ip_pool_repo.py
```

## External API Proxy Rule

All external web API calls must be implemented inside the `core/proxy/` layer.

Services must not use raw HTTP libraries, SDK clients, or direct external API calls.

This applies to every external API, including simple services such as KeyVal-style key/value APIs.

For a KeyVal-style external API, use a descriptive proxy name such as:

```text
core/proxy/key_val_store_proxy.py
```

The service should call clean domain methods exposed by the proxy.

The proxy should handle:

- external endpoint URLs
- HTTP method choice
- request payload construction
- request headers
- timeout configuration
- response parsing
- response mapping
- provider-specific errors

The service should handle:

- business rules
- when data should be saved
- what the stored data means
- how the external API result affects the Elastic IP pool
- whether a proxy/IP resource should be used, retried, failed, or ignored

## Raw Example Rule

The `raw/` folder is used for safe implementation examples, request samples, and expected input/output documentation.

For every proxy named `some_thing_proxy`, create this structure:

```text
raw/
  proxy/
    some_thing_proxy/
      request.txt
      json/
        input.json
        output.json
```

For example, this proxy:

```text
core/proxy/elastic_ip_health_check_proxy.py
```

Must have this raw example structure:

```text
raw/
  proxy/
    elastic_ip_health_check_proxy/
      request.txt
      json/
        input.json
        output.json
```

For a KeyVal-style proxy:

```text
core/proxy/key_val_store_proxy.py
```

The matching raw example structure must be:

```text
raw/
  proxy/
    key_val_store_proxy/
      request.txt
      json/
        input.json
        output.json
```

Required files:

- `request.txt` must contain at least one example request description.
- `json/input.json` must contain at least one valid example input payload.
- `json/output.json` must contain at least one valid example output payload.

`request.txt` should include:

- endpoint or target URL
- HTTP method
- required headers if needed
- short explanation of what the request does
- notes about authentication placeholders if applicable

Raw examples must use realistic but safe sample data.

Do not include:

- real credentials
- real tokens
- API keys
- proxy passwords
- private IPs
- sensitive provider data
- session cookies
- private keys
- cloud credentials

If the proxy class changes its request or response format, update the matching raw example files in the same change.

## Testing Rules

Add unit tests with placeholder test cases only in the first setup phase.

Use the same structure as `core`.

Tests may be marked as skipped or expected failure until implementation exists.

Do not create tests that require:

- real proxy providers
- real cloud credentials
- paid external services
- internet access
- live AWS/GCP/Azure calls
- real Elastic IP ownership
- real private infrastructure

## Safety Rules

Do not commit secrets.

Do not hardcode real proxy credentials.

Do not add `.env` files to git.

Do not commit:

- provider secrets
- cloud credentials
- proxy usernames
- proxy passwords
- tokens
- session cookies
- private keys
- private IPs
- production request dumps
- customer data
- sensitive provider data

Do not implement:

- abuse workflows
- ban bypass
- scraping evasion
- restriction bypass
- CAPTCHA bypass
- account creation abuse
- rate-limit bypass logic
- credential stuffing
- spam automation
- stealth or evasion mechanisms

This project is for legitimate proxy/IP health checking, infrastructure management, clean service architecture, and safe external API abstraction.

## First Milestone

Create only the project skeleton, interfaces, placeholder classes, constants, and placeholder tests.

Do not implement real Elastic IP validation, proxy validation, cloud integration, provider integration, or external API behavior yet.

Expected first structure:

```text
core/
  constant/
    elastic_ip_pool_constant.py
  helper/
    ip_address_format_helper.py
  proxy/
    elastic_ip_health_check_proxy.py
    key_val_store_proxy.py
  service/
    elastic_ip_pool_service.py
  repo/
    elastic_ip_pool_repo.py

test/
  constant/
    test_elastic_ip_pool_constant.py
  helper/
    test_ip_address_format_helper.py
  proxy/
    test_elastic_ip_health_check_proxy.py
    test_key_val_store_proxy.py
  service/
    test_elastic_ip_pool_service.py
  repo/
    test_elastic_ip_pool_repo.py

raw/
  proxy/
    elastic_ip_health_check_proxy/
      request.txt
      json/
        input.json
        output.json
    key_val_store_proxy/
      request.txt
      json/
        input.json
        output.json
```

## Second Milestone

Implement an in-memory Elastic IP pool repo.

Implement basic placeholder-safe validation logic without calling real paid providers.

Implement simple selection rules:

- return only active resources
- skip failed resources
- track failure count
- mark resource unavailable after max failures
- return no available resource when the pool is empty or all resources are unavailable

## Third Milestone

Add persistent storage only after the service layer is stable.

Possible storage options:

- local JSON file
- SQLite
- PostgreSQL
- Redis

Do not add cloud/provider integration until the repo and service contracts are stable.

## Fourth Milestone

Add real external provider integration through the proxy layer only.

When adding a real provider proxy, also add the required raw example contract files under:

```text
raw/proxy/<proxy_name>/
```

The service must call the proxy class.

The service must not directly call external provider APIs.

## Completion Checklist

Before finishing any task, verify:

- N-layer structure is respected.
- Singular naming is used.
- File names are descriptive.
- Constants use UPPER_SNAKE_CASE and type suffixes.
- Service contains business logic only.
- Repo contains data access only.
- Proxy contains external API abstraction only.
- Helper contains generic reusable utility logic only.
- Tests do not call real external providers.
- No credentials or secrets are committed.
- New or modified proxy classes include matching raw examples.
- Raw example JSON files are valid JSON.
- Raw examples do not expose secrets or sensitive data.
