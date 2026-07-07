import base64
import binascii
import json
from json import JSONDecodeError


def decodeBase64JsonValue(encodedValueStr: str | None):
    if not encodedValueStr:
        return None

    try:
        decodedByte = base64.b64decode(
            str(encodedValueStr).encode("utf-8"),
            validate=True,
        )
        decodedValueStr = decodedByte.decode("utf-8")
        return json.loads(decodedValueStr)
    except (JSONDecodeError, UnicodeDecodeError, binascii.Error, ValueError, TypeError):
        return None


def decodeBase64JsonObject(encodedValueStr: str | None) -> dict | None:
    decodedValue = decodeBase64JsonValue(encodedValueStr)
    if isinstance(decodedValue, dict):
        return decodedValue

    return None


def parseJsonValue(jsonValueStr: str | None):
    if not jsonValueStr:
        return None

    try:
        return json.loads(str(jsonValueStr))
    except (JSONDecodeError, TypeError, ValueError):
        return None
