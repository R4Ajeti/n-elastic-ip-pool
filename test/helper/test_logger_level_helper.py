import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from n_elastic_ip_pool.helper.logger_level_helper import getLoggerLevelNameFromEnv


class LoggerLevelHelperTest(unittest.TestCase):
    def getLoggerLevelName(self, envFilePathStr: str) -> str:
        return getLoggerLevelNameFromEnv(
            "LOGGER",
            "DEBUGGING",
            "INFO",
            envFilePathStr,
        )

    def testDebuggingTrueOverridesLoggerInfo(self) -> None:
        with patch.dict(
            os.environ,
            {"DEBUGGING": "true", "LOGGER": "info"},
            clear=True,
        ):
            levelNameStr = self.getLoggerLevelName("missing.env")

        self.assertEqual(levelNameStr, "DEBUG")

    def testDebuggingFalseOverridesLoggerDebug(self) -> None:
        with patch.dict(
            os.environ,
            {"DEBUGGING": "false", "LOGGER": "debug"},
            clear=True,
        ):
            levelNameStr = self.getLoggerLevelName("missing.env")

        self.assertEqual(levelNameStr, "INFO")

    def testLoggerIsUsedWhenDebuggingIsMissing(self) -> None:
        with patch.dict(os.environ, {"LOGGER": "debug"}, clear=True):
            levelNameStr = self.getLoggerLevelName("missing.env")

        self.assertEqual(levelNameStr, "DEBUG")

    def testBlankProcessDebuggingFallsBackToProcessLogger(self) -> None:
        with tempfile.TemporaryDirectory() as temporaryDirectoryStr:
            envFilePath = Path(temporaryDirectoryStr) / ".env"
            envFilePath.write_text(
                "DEBUGGING=true\nLOGGER=debug\n",
                encoding="utf-8",
            )
            with patch.dict(
                os.environ,
                {"DEBUGGING": " ", "LOGGER": "info"},
                clear=True,
            ):
                levelNameStr = self.getLoggerLevelName(str(envFilePath))

        self.assertEqual(levelNameStr, "INFO")

    def testDotEnvValuesUseDebuggingPrecedence(self) -> None:
        with tempfile.TemporaryDirectory() as temporaryDirectoryStr:
            envFilePath = Path(temporaryDirectoryStr) / ".env"
            envFilePath.write_text(
                "DEBUGGING=true\nLOGGER=info\n",
                encoding="utf-8",
            )
            with patch.dict(os.environ, {}, clear=True):
                levelNameStr = self.getLoggerLevelName(str(envFilePath))

        self.assertEqual(levelNameStr, "DEBUG")


if __name__ == "__main__":
    unittest.main()
