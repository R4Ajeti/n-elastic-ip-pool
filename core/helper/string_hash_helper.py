import hashlib


def hashStringValue(valueStr: str) -> str:
    """Return a deterministic SHA-256 hash for a string value."""
    if not isinstance(valueStr, str):
        raise TypeError("valueStr must be a string.")

    return hashlib.sha256(valueStr.encode("utf-8")).hexdigest()
