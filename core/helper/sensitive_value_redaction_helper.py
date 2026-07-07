import re
from urllib.parse import urlsplit, urlunsplit


NETWORK_LOCATION_PATTERN = re.compile(
    r"(?P<host>[A-Za-z0-9.-]+\.[A-Za-z]{2,}|(?:\d{1,3}\.){3}\d{1,3}):(?P<port>\d{1,5})",
)


def redactNetworkLocationValue(value) -> str:
    valueStr = str(value or "")
    if not valueStr:
        return "[redacted]"

    return NETWORK_LOCATION_PATTERN.sub("[redacted-network-location]", valueStr)


def redactUrlPathValue(value) -> str:
    valueStr = str(value or "")
    if not valueStr:
        return "[redacted-url]"

    parsedUrl = urlsplit(valueStr)
    if not parsedUrl.scheme or not parsedUrl.netloc:
        return redactNetworkLocationValue(valueStr)

    redactedUrlStr = urlunsplit(
        (
            parsedUrl.scheme,
            parsedUrl.netloc,
            "/[redacted]",
            "",
            "",
        ),
    )
    return redactNetworkLocationValue(redactedUrlStr)
