import os

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
