---
name: test-placeholder
description: Use this when creating placeholder unit tests for the project without implementing real proxy logic.
---

# Test Placeholder Skill

## Goal

Create placeholder unit tests matching the `core` structure.

## Required Structure

```text
test/
  constant/
  helper/
  proxy/
  service/
  repo/
```

## Rules

- Do not call real proxy providers.
- Do not call real cloud services.
- Do not require internet access.
- Do not require credentials.
- Use skipped or expected-failure tests when implementation is missing.
- Keep test names clear and future-focused.
- Tests should document intended behavior before implementation exists.

## Example Test Intent

- proxy service should return only working proxy
- proxy service should skip failed proxy
- proxy service should mark failed proxy
- repo should save proxy status
- repo should return active proxy list
- proxy client should validate proxy health later
- helper should validate proxy format later

## Output Requirement

Show test files created and explain which tests are placeholders.
