import os

from n_log_forge import configure, setPackageLevel

from n_elastic_ip_pool.helper.env_value_helper import getDotEnvValue


def getLoggerLevelNameFromEnv(
    loggerEnvNameStr: str,
    debuggingEnvNameStr: str,
    defaultLoggerLevelStr: str,
    envFilePathStr: str = ".env",
) -> str:
    debuggingValueStr = os.environ.get(debuggingEnvNameStr)
    if debuggingValueStr is None:
        debuggingValueStr = getDotEnvValue(
            envFilePathStr,
            debuggingEnvNameStr,
        )

    debuggingValueStr = str(debuggingValueStr or "").strip().lower()
    if debuggingValueStr:
        return "DEBUG" if debuggingValueStr == "true" else "INFO"

    loggerLevelStr = os.environ.get(loggerEnvNameStr)
    if loggerLevelStr is None:
        loggerLevelStr = getDotEnvValue(
            envFilePathStr,
            loggerEnvNameStr,
        )

    loggerLevelStr = str(loggerLevelStr or defaultLoggerLevelStr).strip().upper()
    return loggerLevelStr or defaultLoggerLevelStr


def configureLoggingFromEnv(
    loggerNameStr: str,
    loggerLevelStr: str,
    envFilePathStr: str = ".env",
) -> None:
    """Configure n-log-forge, including supported values from the local env file."""
    optionByEnvironmentNameDict = {
        "SENTRY_DATA_SOURCE_NAME": "sentryDataSourceName",
        "SENTRY_ENVIRONMENT": "sentryEnvironment",
        "SENTRY_RELEASE": "sentryRelease",
        "SENTRY_LEVEL": "sentryLevel",
    }
    optionDict: dict[str, str] = {}
    for environmentNameStr, optionNameStr in optionByEnvironmentNameDict.items():
        valueStr = os.environ.get(environmentNameStr)
        if valueStr is None:
            valueStr = getDotEnvValue(envFilePathStr, environmentNameStr)
        if valueStr is not None and valueStr.strip():
            optionDict[optionNameStr] = valueStr.strip()

    originalLoggerValueStr = os.environ.get("LOGGER")
    originalDebuggingValueStr = os.environ.get("DEBUGGING")
    try:
        if originalLoggerValueStr is not None:
            os.environ["LOGGER"] = loggerLevelStr
        if originalDebuggingValueStr is not None and originalDebuggingValueStr.strip():
            os.environ["DEBUGGING"] = (
                "true" if originalDebuggingValueStr.strip().lower() == "true" else "false"
            )
        configure(level=loggerLevelStr, manageRootLevel=False, **optionDict)
    finally:
        if originalLoggerValueStr is None:
            os.environ.pop("LOGGER", None)
        else:
            os.environ["LOGGER"] = originalLoggerValueStr
        if originalDebuggingValueStr is None:
            os.environ.pop("DEBUGGING", None)
        else:
            os.environ["DEBUGGING"] = originalDebuggingValueStr
    setPackageLevel(loggerNameStr, loggerLevelStr)
