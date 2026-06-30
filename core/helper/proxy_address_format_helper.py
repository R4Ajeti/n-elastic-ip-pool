import re
from urllib.parse import urlsplit

_DOMAIN_LABEL_PATTERN = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$")


def normalizeProxyAddress(proxyAddressStr: str) -> str | None:
    """Return a clean host:port proxy address when the value is reusable."""
    if not isinstance(proxyAddressStr, str):
        return None

    cleanedProxyAddressStr = proxyAddressStr.strip()
    if not cleanedProxyAddressStr or any(char.isspace() for char in cleanedProxyAddressStr):
        return None

    parsedProxyAddress = urlsplit(cleanedProxyAddressStr)
    if "://" in cleanedProxyAddressStr:
        if parsedProxyAddress.scheme not in {"http", "https"}:
            return None
        if parsedProxyAddress.username or parsedProxyAddress.password:
            return None
        hostStr = parsedProxyAddress.hostname
        try:
            portInt = parsedProxyAddress.port
        except ValueError:
            return None
    else:
        if cleanedProxyAddressStr.count(":") != 1:
            return None
        hostStr, portTextStr = cleanedProxyAddressStr.rsplit(":", 1)
        hostStr = hostStr.strip("[]")
        if not portTextStr.isdigit():
            return None
        portInt = int(portTextStr)

    if not hostStr or not portInt:
        return None

    if portInt < 1 or portInt > 65535:
        return None

    hostStr = hostStr.lower()
    if not _isHostFormatValid(hostStr):
        return None

    return f"{hostStr}:{portInt}"


def isProxyAddressFormatValid(proxyAddressStr: str) -> bool:
    """Return whether a proxy address can be normalized to host:port."""
    return normalizeProxyAddress(proxyAddressStr) is not None


def _isHostFormatValid(hostStr: str) -> bool:
    if len(hostStr) > 253:
        return False

    if _isIpv4AddressFormatValid(hostStr):
        return True

    labelList = hostStr.rstrip(".").split(".")
    if len(labelList) < 2:
        return False

    return all(_DOMAIN_LABEL_PATTERN.match(labelStr) for labelStr in labelList)


def _isIpv4AddressFormatValid(hostStr: str) -> bool:
    octetList = hostStr.split(".")
    if len(octetList) != 4:
        return False

    for octetStr in octetList:
        if not octetStr.isdigit():
            return False
        if len(octetStr) > 1 and octetStr.startswith("0"):
            return False
        octetInt = int(octetStr)
        if octetInt < 0 or octetInt > 255:
            return False

    return True
