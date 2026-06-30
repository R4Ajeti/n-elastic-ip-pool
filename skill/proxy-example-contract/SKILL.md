---
name: proxy-example-contract
description: Use this when implementing or modifying a proxy class to ensure matching raw request/input/output examples are included.
---

# Proxy Example Contract Skill

## Goal

Whenever a new proxy class is implemented, it must include a matching raw example folder that documents at least one safe usage example.

A proxy implementation is not considered complete unless the raw example files are added or updated.

## Required Structure

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

## Required Files

### request.txt

`request.txt` must contain at least one example request description.

It should include:

- endpoint or target URL
- HTTP method
- required headers if needed
- short explanation of what the request does
- notes about authentication placeholders if applicable

### json/input.json

`json/input.json` must contain at least one valid example input payload.

The input should be realistic enough to explain how the proxy class is used.

### json/output.json

`json/output.json` must contain at least one valid example output payload.

The output should match the expected response shape returned by the proxy class.

## Rules

- Use realistic but safe sample data.
- Do not include real credentials.
- Do not include real tokens.
- Do not include API keys.
- Do not include proxy passwords.
- Do not include private IPs.
- Do not include sensitive provider data.
- Keep the raw example aligned with the implemented proxy class.
- If the proxy class changes its request format, update the matching raw example files.
- If the proxy class changes its response format, update the matching raw example files.
- Do not consider a proxy implementation complete unless these raw example files are added.

## Example

For a proxy class file like:

```text
core/proxy/some_thing_proxy.py
```

The matching raw example must be:

```text
raw/proxy/some_thing_proxy/request.txt
raw/proxy/some_thing_proxy/json/input.json
raw/proxy/some_thing_proxy/json/output.json
```

## Review Checklist

Before completing the task, verify:

- The proxy class exists.
- The matching raw folder exists.
- `request.txt` exists.
- `json/input.json` exists.
- `json/output.json` exists.
- JSON files are valid JSON.
- Example data is safe and does not expose secrets.
- Raw examples match the proxy class behavior.
