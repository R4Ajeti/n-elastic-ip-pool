"""Public package namespace for the n_elastic_ip_pool project."""

from pathlib import Path

_SOURCE_CORE_PATH = Path(__file__).resolve().parent.parent / "core"
if _SOURCE_CORE_PATH.is_dir():
    __path__.append(str(_SOURCE_CORE_PATH))

__all__ = [
    "constant",
    "helper",
    "proxy",
    "repo",
    "service",
]
