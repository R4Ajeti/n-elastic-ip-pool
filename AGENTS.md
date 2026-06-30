# AGENTS.md

## Project

Project name: `n_elastic_ip_pool`

This is a low-level Python project for managing an IP/proxy pool and returning only working, validated proxy resources.

## Codex Instructions

Before making changes, read this file and follow the relevant skill from the `skill/` directory.

Use repository skills for repeatable workflows:

- `skill/n-layer-scaffold/SKILL.md`
- `skill/service-boundary-review/SKILL.md`
- `skill/test-placeholder/SKILL.md`

If Codex native skill discovery is available, use the `.agents/skills` symlink, which points to `skill/`.

## Architecture

Use N-layer programming.

Required flow:

```text
Controller or Entry Point → Service → Repo / Proxy Client → Storage / External Provider
```

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
- `MAX_PROXY_FAILURE_COUNT_INT`
- `PROXY_HEALTH_CHECK_URL_STR`

## Layer Rules

### constant

Store constants only.

Do not store business logic.

Use descriptive names.

Split constants into subfolders when a file becomes too large or mixes multiple domains.

### helper

Store only generic reusable functions.

Helpers must not contain business rules, company-specific logic, credentials, provider-specific behavior, or sensitive implementation details.

### proxy

Store external client/provider communication logic.

This can include future communication with cloud providers, proxy providers, health-check endpoints, or external APIs.

Do not put business decisions here.

### service

Store business logic.

The service decides which proxy is usable, when to retry, when to mark a proxy as failed, and when to return no proxy.

Do not put raw database queries here.

### repo

Store data access logic.

The repo hides storage details from the service.

The first version may use placeholder methods only.

## Testing Rules

Add unit tests with placeholder test cases only in the first setup phase.

Use the same structure as `core`.

Tests may be marked as skipped or expected failure until implementation exists.

Do not create tests that require real proxy providers, real cloud credentials, or paid external services.

## Safety Rules

Do not commit secrets.

Do not hardcode real proxy credentials.

Do not add `.env` files to git.

Do not implement abuse, ban bypass, scraping evasion, or restriction bypass logic.

This project is for legitimate proxy/IP health checking, infrastructure management, and clean service architecture.

## First Milestone

Create only the project skeleton, interfaces, placeholder classes, constants, and placeholder tests.

Do not implement real proxy validation logic yet.

## Second Milestone

Implement an in-memory proxy repo.

Implement basic proxy validation using a safe health-check URL.

Implement simple selection rules:

- return only active proxies
- skip failed proxies
- track failure count
- mark proxy unavailable after max failures

## Third Milestone

Add persistent storage or provider integration only after the service layer is stable.
