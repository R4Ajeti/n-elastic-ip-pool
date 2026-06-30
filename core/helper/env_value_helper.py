import os
from pathlib import Path


def getEnvValue(
    envNameStr: str,
    defaultValueStr: str,
    envFilePathStr: str = ".env",
) -> str:
    envValueStr = os.environ.get(envNameStr)
    if envValueStr:
        return envValueStr

    dotEnvValueStr = getDotEnvValue(envFilePathStr, envNameStr)
    if dotEnvValueStr:
        return dotEnvValueStr

    return defaultValueStr


def getDotEnvValue(envFilePathStr: str, envNameStr: str) -> str | None:
    envFilePath = Path(envFilePathStr)
    if not envFilePath.exists() or not envFilePath.is_file():
        return None

    for lineStr in envFilePath.read_text(encoding="utf-8").splitlines():
        cleanedLineStr = lineStr.strip()
        if not cleanedLineStr or cleanedLineStr.startswith("#"):
            continue

        if cleanedLineStr.startswith("export "):
            cleanedLineStr = cleanedLineStr.removeprefix("export ").strip()

        keyStr, separatorStr, valueStr = cleanedLineStr.partition("=")
        if separatorStr and keyStr.strip() == envNameStr:
            return valueStr.strip().strip("'\"")

    return None
