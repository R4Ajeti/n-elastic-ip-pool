import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from n_elastic_ip_pool.constant.elastic_ip_pool_constant import KEY_VAL_STORE_PROXY_ENV_NAME_STR
from n_elastic_ip_pool.helper.env_value_helper import getEnvIntValue, getEnvValue


class EnvValueHelperTest(unittest.TestCase):
    def testGetEnvIntValueReturnsConfiguredInteger(self) -> None:
        with patch.dict(os.environ, {"SAMPLE_TIMEOUT": "1250"}, clear=True):
            resultInt = getEnvIntValue("SAMPLE_TIMEOUT", 2000, "missing.env")

        self.assertEqual(resultInt, 1250)

    def testGetEnvIntValueFallsBackForInvalidValue(self) -> None:
        with patch.dict(os.environ, {"SAMPLE_TIMEOUT": "invalid"}, clear=True):
            resultInt = getEnvIntValue("SAMPLE_TIMEOUT", 2000, "missing.env")

        self.assertEqual(resultInt, 2000)

    def testGetEnvValueIgnoresInlineCommentAfterBlankValue(self) -> None:
        with tempfile.TemporaryDirectory() as temporaryDirectoryStr:
            envPath = Path(temporaryDirectoryStr) / ".env"
            envPath.write_text(
                "SAMPLE_VALUE= # Optional setting.\n",
                encoding="utf-8",
            )
            with patch.dict(os.environ, {}, clear=True):
                resultStr = getEnvValue(
                    "SAMPLE_VALUE",
                    "fallback",
                    str(envPath),
                )

        self.assertEqual(resultStr, "fallback")

    def testGetEnvValueReturnsProcessEnvironmentValue(self) -> None:
        with patch.dict(os.environ, {KEY_VAL_STORE_PROXY_ENV_NAME_STR: "from-process"}):
            resultStr = getEnvValue(KEY_VAL_STORE_PROXY_ENV_NAME_STR, "from-default")

        self.assertEqual(resultStr, "from-process")

    def testGetEnvValueReturnsDotEnvValue(self) -> None:
        with tempfile.TemporaryDirectory() as tempDirStr:
            envFilePath = Path(tempDirStr) / ".env"
            envFilePath.write_text(
                f"{KEY_VAL_STORE_PROXY_ENV_NAME_STR}=from-dot-env\n",
                encoding="utf-8",
            )

            with patch.dict(os.environ, {}, clear=True):
                resultStr = getEnvValue(
                    KEY_VAL_STORE_PROXY_ENV_NAME_STR,
                    "from-default",
                    str(envFilePath),
                )

        self.assertEqual(resultStr, "from-dot-env")

    def testGetEnvValueReturnsDefaultValue(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            resultStr = getEnvValue(
                KEY_VAL_STORE_PROXY_ENV_NAME_STR,
                "from-default",
                "missing.env",
            )

        self.assertEqual(resultStr, "from-default")


if __name__ == "__main__":
    unittest.main()
