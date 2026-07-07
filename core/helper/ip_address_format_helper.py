import ipaddress


def isIpAddressFormatValid(ipAddressStr: str) -> bool:
    """Return whether a value is a valid IPv4 or IPv6 address string."""
    if not isinstance(ipAddressStr, str):
        return False

    cleanedIpAddressStr = ipAddressStr.strip()
    if not cleanedIpAddressStr or cleanedIpAddressStr != ipAddressStr:
        return False

    try:
        ipaddress.ip_address(cleanedIpAddressStr)
    except ValueError:
        return False

    return True
