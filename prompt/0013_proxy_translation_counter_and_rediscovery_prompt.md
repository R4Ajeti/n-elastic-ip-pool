# 013 - Proxy Translation Counter and Rediscovery

Follow `AGENTS.md` and `skill/service-boundary-review/SKILL.md`. Follow
`skill/proxy-example-contract/SKILL.md` if a proxy class changes.

## Goal

Track successful subtitle translations and proxy-caused translation failures
using a signed integer in the existing KeyVal database. Rediscover working
proxies when the configured upper or lower threshold is reached. Preserve
existing public methods and unrelated behavior.

Save this prompt before changing implementation files.

## Configuration

Support process environment and `.env` configuration, with explicit constructor
arguments taking precedence:

- `KEY_VAL_PROXY_TRANSLATION_COUNT_KEY`: meaningful counter key namespace;
  default to `n-elastic-ip-pool-proxy-translation-count`.
- `PROXY_TRANSLATION_MAX_USE_COUNT`: upper threshold; default `50`.
- `PROXY_TRANSLATION_MIN_HEALTH_COUNT`: lower threshold; default `-5`.

Use typed constants, meaningful camelCase Python parameter names, and safe
fallbacks for missing, blank, malformed, or wrong-sign threshold values.
Keep the existing proxy-cache namespace and storage configuration compatible.
Document settings in `env_example` and `README.md`; never commit `.env`.

## Counter and Translation Result Contract

- Start an absent counter at zero. Store plain signed decimal integer values,
  such as `0`, `1`, `50`, `999`, or `-5`, using the existing KeyVal abstraction.
- Scope counter keys by configured namespace, pool, and proxy so a replacement
  never inherits another proxy's counter. Expose a way to obtain the storage key.
- Add one after a subtitle translation actually succeeds.
- Subtract one only when translation fails because of the proxy.
- Do not count discovery, selection, health checks, or unrelated translation
  failures as subtitle outcomes.
- This repository has no subtitle translation implementation. Provide and
  document an explicit result-reporting method for the consuming translator;
  do not claim the external application's call sites have been changed.
- Preserve the existing usage-history API separately for compatibility.
- Explain that this is a net success-minus-proxy-failure count, not two
  independent counters or a consecutive-failure count.

## Rediscovery

- At or above the upper threshold, or at or below the lower threshold, run
  fresh discovery immediately and return the replacement proxy or `None`.
- Exclude exhausted/failing proxies from saved-cache and discovery results,
  including after restart when persisted counters are available.
- Do not automatically retry a subtitle, bypass provider restrictions, or
  introduce rate-limit bypass behavior.
- Prevent KeyVal failures from masking a completed translation. Retain local
  counter progress and enforce thresholds when persistence is unavailable;
  document persistence and concurrency limitations.
- Keep verbose result state consistent after rediscovery.

## Architecture and Examples

Keep counter/selection business rules in the service, HTTP calls in the proxy,
and generic parsing in helpers. Reuse the existing KeyVal request contract.
Include safe numeric counter examples under `raw/proxy/key_val_store_proxy/`.
Never expose credentials, sensitive keys, or real infrastructure in examples.

## Verification and Release

Add offline regression tests for configuration precedence/defaults, numeric
persistence, success/failure accounting, threshold boundaries and overshoots,
cache exclusion, fresh discovery, replacement isolation, storage failures,
verbose result state, and existing behavior. Tests must not call live providers.

Validate raw JSON, run the full test suite, inspect the diff for secrets and
architecture violations, and verify package metadata. Bump the patch version
from `1.0.2` to `1.0.3`. Commit and push the completed changes to the current
branch without overwriting unrelated user work or force-pushing.
