import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.constant.elastic_ip_pool_constant import KEY_VAL_STORE_PROXY_ENV_NAME_STR
from core.helper.env_value_helper import getEnvValue


class EnvValueHelperTest(unittest.TestCase):
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
