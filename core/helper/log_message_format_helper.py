"""Generic formatting for printable log records without configuring handlers."""

import logging


def formatLogMessage(
    messageStr: str, loggerNameStr: str, levelStr: str, formatStr: str,
) -> str:
    record = logging.LogRecord(
        loggerNameStr, getattr(logging, levelStr), "", 0, messageStr, (), None,
    )
    return logging.Formatter(formatStr).format(record)
