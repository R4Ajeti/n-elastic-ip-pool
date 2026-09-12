# Migrate logging to n-log-forge

## Outcome and scope

Migrate `n-proxy` from its custom printable logging and isolated Sentry Logs
adapter to the shared `n-log-forge` package. Preserve the verbose proxy
discovery narrative, redaction guarantees, `DEBUGGING`/`LOGGER` behavior,
exception tracebacks, and all non-logging application behavior.

Use the public `n_log_forge` API only. Prefer automatic source/package
identification and use an explicit package-name override only if verification
shows that the public package layout cannot produce the required `n-proxy`
label. Do not recreate console formatting, Sentry transport, timing, lifecycle,
or handler management already supplied by `n-log-forge`.

## Baseline

- Baseline revision: `f50194d` on `main`; the working tree was clean before this
  prompt was created.
- Previous prompt: [`0017_optional_sentry_logs.md`](0017_optional_sentry_logs.md).
- The existing prompt filenames use a legacy four-digit sequence. This prompt
  continues the numeric sequence as `000018` while adopting the required
  six-digit filename format.
- Shared logger reference: sibling repository `../n-log-forge` at revision
  `2b425c4`, especially its `README.md`, public facade, source attribution,
  event snapshotting, console provider, timing, and lifecycle implementation.

## Coverage

| Change / requirement | Evidence | Current state | Next action |
| --- | --- | --- | --- |
| Centralize logging in `n-log-forge` | User request; `core/service/verbose_elastic_ip_pool_service.py` | Implemented | Shared facade, configuration, and timers now own active logging |
| Preserve package identity | `CORE_LOGGER_NAME_STR`; emitted console record | Verified | PACKAGE renders as `N Proxy`; SOURCE retains the module hierarchy |
| Preserve safe verbose messages | Verbose service and redaction helpers | Verified | Existing messages/redaction are retained through the shared facade |
| Remove obsolete custom logging | Formatter, Sentry proxy/constants/raw/tests | Implemented | Redundant local artifacts were removed after consumers were migrated |
| Required dependency | `pyproject.toml`, `requirements.txt` | Verified | Both formats require `n-log-forge[sentry]`; Python metadata is 3.14+ |
| Offline verification | Repository tests and wheel build | Verified | 164 tests passed, 2 skipped; wheel metadata and whitespace checks passed |

## Implementation plan

1. Follow `AGENTS.md` and the applicable repository skills. Inventory every
   logging call, custom logger helper, Sentry adapter, environment setting,
   test, README section, raw example, app entry point, and dependency declaration.
2. Route verbose service events through `n_log_forge.getLogger(__name__)` (or the
   global facade when caller-based detection is more accurate). Preserve lazy
   formatting, redacted proxy values, useful fields, and exception information.
3. Use `n-log-forge` timing/lifecycle/configuration where it replaces manual
   timing and Sentry ownership without altering discovery behavior. Retain the
   established environment semantics, including `.env`-backed values where this
   package intentionally supports them.
4. Delete legacy formatting and Sentry code/constants/tests/raw contracts only
   after references are gone. Update public docs and environment examples to the
   `n-log-forge` names and behavior.
5. Add the required dependency to both supported dependency declarations. Keep
   declared Python compatibility truthful to the dependency's Python 3.14 floor.

## Acceptance and verification

- Operational logs flow through `n-log-forge` and display `n-proxy` as the
  originating package while preserving meaningful module/source attribution.
- `DEBUGGING`/`LOGGER`, optional Sentry delivery, safe metadata, tracebacks, and
  verbose discovery output remain functional with no duplicate handlers/events.
- No custom formatter, Sentry client/handler, or redundant logging lifecycle
  remains in active code.
- All deterministic tests pass (document pre-existing failures separately), the
  wheel metadata contains the required dependency, imports work on the supported
  Python version, and `git diff --check` is clean.

## Implementation result

The migration is complete. The verbose service and standalone request-limit
diagnostic use `n-log-forge`; environment-based levels and optional Sentry are
delegated through the shared configuration API; operation timing uses the
shared timer; and obsolete formatter/Sentry code was removed. README and env
examples describe the new output and settings. The adjacent `n-log-forge`
package was also made namespace-safe so it no longer installs a conflicting
top-level `core` package.
