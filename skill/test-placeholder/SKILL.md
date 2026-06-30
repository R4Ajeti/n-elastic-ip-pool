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

- elastic IP pool service should return only working proxy resources
- elastic IP pool service should skip failed proxy resources
- elastic IP pool service should mark failed proxy resources
- elastic IP pool repo should save resource status
- elastic IP pool repo should return active resource list
- elastic IP health check proxy should validate proxy health later
- key val store proxy should persist provider state later
- helper should validate IP address format later

## Output Requirement

Show test files created and explain which tests are placeholders.
