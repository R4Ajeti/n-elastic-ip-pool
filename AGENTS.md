# AGENTS.md

## Project

Project name: `n_elastic_ip_pool`

This is a low-level Python project for managing an IP/proxy pool and returning only working, validated proxy resources.

## Codex Instructions

Before making changes, read this file and follow the relevant skill from the `skill/` directory.

Use repository skills for repeatable workflows:

* `skill/n-layer-scaffold/SKILL.md`
* `skill/service-boundary-review/SKILL.md`
* `skill/test-placeholder/SKILL.md`

If Codex native skill discovery is available, use the `.agents/skills` symlink, which points to `skill/`.

## Architecture

Use N-layer programming.

Required flow:

Controller or Entry Point → Service → Repo / Proxy Client → Storage / External Provider

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

* CORE_LOGGER_NAME_STR
* DEFAULT_TIMEOUT_SECOND_INT
* MAX_PROXY_FAILURE_COUNT_INT
* PROXY_HEALTH_CHECK_URL_STR

## Safety Rules

Do not commit secrets.

Do not hardcode real proxy credentials.

Do not add `.env` files to git.

Do not implement abuse, ban bypass, scraping evasion, or restriction bypass logic.

This project is for legitimate proxy/IP health checking, infrastructure management, and clean service architecture.

## First Milestone

Create only the project skeleton, interfaces, placeholder classes, constants, and placeholder tests.

Do not implement real proxy validation logic yet.


