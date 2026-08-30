# 014 - Reset Proxy Translation Counters After Fresh Discovery

Follow `AGENTS.md` and `skill/service-boundary-review/SKILL.md`.
Save this prompt before implementation changes.

## Clarification

When finding IP addresses from the beginning succeeds, start a new translation
counter cycle at zero for each validated proxy returned by fresh discovery.
This supplements prompt 0013. Do not reset on cache checks, failed discovery,
or individual health checks. Do not erase counters belonging to rejected or
unrelated proxies, and retain existing exhausted-proxy exclusion rules.

## Implementation

- Reset counters for the final ranked working proxy list, including fallback
  provider discovery and discovery triggered by either translation threshold.
- Store the numeric value `0` through the existing KeyVal proxy and update local
  state. Respect disabled persistence and read-only settings.
- If persistence fails, retain the local reset and retry persistence on later
  translation feedback. Do not prevent returning a validated proxy.
- Do not change the separate Firebase usage-history contract.
- Log the exact hashed counter storage key at INFO after counter reset/update,
  together with the current number and whether it was saved to KeyVal. The user
  explicitly requested this key for lookup. Never log the unhashed namespace,
  bearer token, credentials, or full provider URL. Use `[translation-count]`
  as the searchable log marker and document how to look up the key.
- Update documentation and offline tests, including positive/negative existing
  counts, fallback discovery, failed searches, cache checks, and storage outages.
- Bump the patch version to 1.0.4, verify the complete test suite and package
  build, then commit and push the follow-up correction.
