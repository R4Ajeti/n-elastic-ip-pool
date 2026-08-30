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


def formatNetworkLocationForLog(value) -> str:
    """Expose only host:port, never URL credentials, paths, queries or fragments."""
    if not isinstance(value, str) or not value or any(char.isspace() for char in value):
        return "[redacted]"
    try:
        parsedUrl = urlsplit(value if "://" in value else f"//{value}")
        hostStr = parsedUrl.hostname
        portInt = parsedUrl.port
    except ValueError:
        return "[redacted]"
    locationStr = f"{hostStr}:{portInt}"
    if not portInt or not NETWORK_LOCATION_PATTERN.fullmatch(locationStr):
        return "[redacted]"
    return locationStr


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
