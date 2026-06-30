# KeyVal Dummy Proxy Flow Prompt

Implement the first placeholder flow for saving and retrieving a dummy proxy using the KeyVal API.

## Context

KeyVal is this website:

```text
https://keyval.org/
```

Search the web and read the KeyVal documentation before implementing the proxy layer.

## Goal

Create a simple service flow where the service can save and retrieve a dummy proxy value using the KeyVal API through the `core/proxy/` layer.

## Architecture Rules

- Follow `AGENTS.md`.
- Follow N-layer architecture.
- Services must not call external APIs directly.
- All KeyVal API calls must be abstracted inside a proxy class.
- Do not add real proxy credentials.
- Do not add real provider credentials.
- Use only safe dummy proxy data.
- Keep the implementation minimal.

## Implementation Requirements

### 1. Add a descriptive dummy proxy constant

The dummy proxy value must be stored in a descriptive constant variable.

The value should not be stored directly in plain text.

Hash the dummy proxy string using a helper function, then store or send the hashed value.

### 2. Add a helper function for hashing strings

Create or update a helper file with a reusable function for hashing strings.

The function should:

- accept a string input
- return a deterministic hash string
- avoid exposing sensitive values
- be generic and reusable

### 3. Add a KeyVal proxy abstraction

Create a proxy class for the KeyVal API.

Example file name:

```text
core/proxy/key_val_store_proxy.py
```

The proxy layer should handle:

- KeyVal endpoint URLs
- request construction
- response parsing
- provider-specific errors
- timeout handling

### 4. Add or update the service

The service should be importable and usable by creating the service class instance and calling its public method:

```text
get()
```

The `get()` method should call an internal method:

```text
check()
```

The `check()` method should verify whether the proxy value already exists in KeyVal for the configured key.

For now, the check is simple:

- if a value exists for the key, treat the proxy as available
- if no value exists, treat the proxy as missing

If `check()` fails, `get()` should call another internal method:

```text
update()
```

The `update()` method should:

- create/use another safe dummy proxy value for now
- hash it using the helper function
- save it to KeyVal through the proxy layer
- return the saved hashed value

### 5. Add raw proxy examples

Because this adds a KeyVal proxy, also add the required raw example files:

```text
raw/proxy/key_val_store_proxy/request.txt
raw/proxy/key_val_store_proxy/json/input.json
raw/proxy/key_val_store_proxy/json/output.json
```

The examples must be safe and must not include real credentials, real tokens, real proxy passwords, private IPs, or sensitive provider data.

### 6. Add or update tests

Add tests for the service flow and helper function.

Tests should not depend on the live KeyVal API unless explicitly isolated or mocked.

Prefer mocking the KeyVal proxy in service tests.

## Expected Behavior

- `get()` calls `check()`
- if `check()` succeeds, return the existing stored proxy value
- if `check()` fails, call `update()`
- `update()` saves a new hashed dummy proxy value through the KeyVal proxy
- services do not call KeyVal directly
- all external API logic stays inside `core/proxy/`

## After Implementation

- Show the final relevant file tree.
- Summarize what files were changed.
- Explain how the service flow works.
- Suggest a descriptive git commit message.
