from n_elastic_ip_pool.helper.env_value_helper import getEnvValue


def getLoggerLevelNameFromEnv(
    loggerEnvNameStr: str,
    debuggingEnvNameStr: str,
    defaultLoggerLevelStr: str,
    envFilePathStr: str = ".env",
) -> str:
    debuggingValueStr = getEnvValue(
        debuggingEnvNameStr,
        "",
        envFilePathStr,
    ).strip().lower()
    if debuggingValueStr:
        return "DEBUG" if debuggingValueStr == "true" else "INFO"

    loggerLevelStr = getEnvValue(
        loggerEnvNameStr,
        defaultLoggerLevelStr,
        envFilePathStr,
    ).strip().upper()
    return loggerLevelStr or defaultLoggerLevelStr
