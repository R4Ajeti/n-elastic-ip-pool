---
name: service-boundary-review
description: Use this when reviewing whether service, repo, proxy, helper, and constant responsibilities are separated correctly.
---

# Service Boundary Review Skill

## Goal

Review architecture boundaries in `n_elastic_ip_pool`.

## Check These Rules

### constant

- Contains constants only.
- Uses UPPER_SNAKE_CASE.
- Constants include type suffixes.
- Does not contain business logic.
- Does not contain runtime calculations.

### helper

- Contains generic reusable utilities only.
- Does not contain business logic.
- Does not contain provider-specific logic.
- Does not contain secrets.
- Can be safely reused outside the project.

### proxy

- Contains external client/provider communication only.
- Does not decide business rules.
- Does not directly expose credentials.
- Does not contain storage logic.

### service

- Contains business logic.
- Coordinates repo and proxy classes.
- Decides which proxy is usable.
- Decides when to retry, mark failed, mark unavailable, or return no proxy.
- Does not contain raw storage/database logic.
- Does not directly expose provider-specific implementation details.

### repo

- Contains data access logic.
- Hides storage details from service.
- Does not contain business rules.
- Does not call external proxy providers directly.

## Output Requirement

Return:

- pass/fail rating
- architecture violations
- recommended refactor steps
- files that should be moved or renamed
