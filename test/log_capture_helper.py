import logging
from contextlib import contextmanager
from unittest.mock import call

from n_elastic_ip_pool.constant.elastic_ip_pool_constant import CORE_LOGGER_NAME_STR


class _RecordCollector(logging.Handler):
    def __init__(self) -> None:
        super().__init__(logging.DEBUG)
        self.messageList: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.messageList.append(
            f"{record.levelname} | {CORE_LOGGER_NAME_STR} | {record.getMessage()}"
        )


class CapturedPackageLogs:
    def __init__(self, collector: _RecordCollector) -> None:
        self.collector = collector
        self.offsetInt = 0

    @property
    def call_args_list(self):
        return [call(messageStr) for messageStr in self.collector.messageList[self.offsetInt:]]

    @property
    def call_args(self):
        callList = self.call_args_list
        return callList[-1] if callList else None

    def reset_mock(self) -> None:
        self.offsetInt = len(self.collector.messageList)

    def assert_not_called(self) -> None:
        if self.call_args_list:
            raise AssertionError(f"Expected no package logs, received {self.call_args_list!r}")


@contextmanager
def capturePackageLogs():
    standardLogger = logging.getLogger(CORE_LOGGER_NAME_STR)
    previousLevelInt = standardLogger.level
    collector = _RecordCollector()
    standardLogger.addHandler(collector)
    standardLogger.setLevel(logging.DEBUG)
    try:
        yield CapturedPackageLogs(collector)
    finally:
        standardLogger.removeHandler(collector)
        standardLogger.setLevel(previousLevelInt)
