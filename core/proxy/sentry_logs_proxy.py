"""Opt-in Sentry Logs transport, isolated from the host application's SDK client."""

import atexit
from functools import lru_cache
import logging
import os
import warnings
from threading import RLock

from n_elastic_ip_pool.constant.sentry_log_constant import (
    SENTRY_DSN_ENV_NAME_STR,
    SENTRY_ENVIRONMENT_ENV_NAME_STR,
    SENTRY_RELEASE_ENV_NAME_STR,
    SENTRY_LOG_LEVEL_ENV_NAME_STR,
    SENTRY_REPOSITORY_NAME_STR,
    SENTRY_DEFAULT_ENVIRONMENT_STR,
    SENTRY_DEFAULT_LOG_LEVEL_STR,
)


class SentryLogsProxy(logging.Handler):
    """Forward only explicit project records; never initialize global integrations."""

    def __init__(self, environmentValueFunc=None):
        super().__init__()
        self.environmentValueFunc = environmentValueFunc or os.getenv
        self.client = None
        self.sdk = None
        self.configurationTuple = None
        self.failedBool = False
        self.stateLock = RLock()
        self.shutdownRegisteredBool = False

    def configure(self):
        values = tuple((self.environmentValueFunc(name) or "").strip() for name in (
            SENTRY_DSN_ENV_NAME_STR, SENTRY_ENVIRONMENT_ENV_NAME_STR,
            SENTRY_RELEASE_ENV_NAME_STR, SENTRY_LOG_LEVEL_ENV_NAME_STR,
        ))
        with self.stateLock:
            if values == self.configurationTuple:
                return self.client is not None
            self.flush()
            if self.client is not None:
                self.client.close()
            self.client = None
            self.configurationTuple = values
            self.failedBool = False
            dsn, environment, release, level = values
            if not dsn:
                return False
            level = level.upper() or SENTRY_DEFAULT_LOG_LEVEL_STR
            self.remoteLevelInt = {
                "DEBUG": 10, "INFO": 20, "WARN": 30, "WARNING": 30,
                "ERROR": 40, "CRITICAL": 50,
            }.get(level, logging.INFO)
            try:
                import sentry_sdk
                from sentry_sdk import logger  # Load the public logging submodule.
                self.sdk = sentry_sdk
                self.client = sentry_sdk.Client(
                    dsn=dsn,
                    environment=environment or SENTRY_DEFAULT_ENVIRONMENT_STR,
                    release=release or None,
                    enable_logs=True,
                    default_integrations=False,
                    auto_enabling_integrations=False,
                    send_default_pii=False,
                    include_local_variables=False,
                    before_send_log=self.prepareLog,
                )
                if not self.shutdownRegisteredBool:
                    atexit.register(self.flush)
                    self.shutdownRegisteredBool = True
            except Exception:
                self.warnFailure()
            return self.client is not None

    def prepareLog(self, log, hint):
        # Only explicitly supplied attributes leave this adapter. Do not forward
        # host scope/user metadata inherited by the temporary SDK scope.
        log["attributes"] = {
            key: value for key, value in log["attributes"].items()
            if key in {"repository", "service.name", "logger.name", "sentry.environment",
                       "sentry.release", "sentry.sdk.name", "sentry.sdk.version"}
        }
        log["attributes"]["repository"] = SENTRY_REPOSITORY_NAME_STR
        log["attributes"]["service.name"] = SENTRY_REPOSITORY_NAME_STR
        return log

    def warnFailure(self):
        if not self.failedBool:
            self.failedBool = True
            warnings.warn(
                "Sentry Logs unavailable for " + SENTRY_REPOSITORY_NAME_STR
                + "; local logging continues. Check Sentry configuration and SDK installation.",
                RuntimeWarning, stacklevel=2,
            )

    def emit(self, record):
        try:
            with self.stateLock:
                if not self.configure() or record.levelno < self.remoteLevelInt:
                    return
                method = ("fatal" if record.levelno >= 50 else "error" if record.levelno >= 40
                          else "warning" if record.levelno >= 30 else "info" if record.levelno >= 20
                          else "debug")
                with self.sdk.new_scope() as scope:
                    scope.set_client(self.client)
                    getattr(self.sdk.logger, method)(
                        "{message}", message=record.getMessage(), attributes={
                            "repository": SENTRY_REPOSITORY_NAME_STR,
                            "service.name": SENTRY_REPOSITORY_NAME_STR,
                            "logger.name": record.name,
                        },
                    )
        except Exception:
            self.warnFailure()

    def captureMessage(self, messageStr, levelStr, loggerNameStr):
        self.handle(logging.LogRecord(
            loggerNameStr, getattr(logging, levelStr), "", 0, messageStr, (), None,
        ))

    def attachLogger(self, logger):
        if self.configure() and self not in logger.handlers:
            logger.addHandler(self)

    def flush(self):
        with self.stateLock:
            if self.client is not None:
                self.client.flush(timeout=2)


sentryLogsProxy = SentryLogsProxy()


@lru_cache(maxsize=None)
def getSentryLogsProxy(envFilePathStr=".env"):
    """Share a transport across services using the same environment file."""
    from n_elastic_ip_pool.helper.env_value_helper import getEnvValue
    return SentryLogsProxy(
        lambda name: os.environ[name] if name in os.environ
        else getEnvValue(name, "", envFilePathStr),
    )
