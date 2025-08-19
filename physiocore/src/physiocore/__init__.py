"""physiocore — physiotherapy exercise toolkit."""

from importlib.metadata import PackageNotFoundError, version as _pkg_version
from importlib import import_module as _import_module
from typing import TYPE_CHECKING

# 1) version: prefer installed package metadata, fallback to static file
try:
    __version__ = _pkg_version(__name__)
except PackageNotFoundError:
    # when developing locally, fall back to the static file
    from ._version import __version__  # type: ignore

# 2) public names we want to expose lazily
__all__ = [
    "__version__",
    "create_tracker",
    "ankle_toe_movement",
    "any_prone_straight_leg_raise",
    "any_straight_leg_raise",
    "bridging",
    "cobra_stretch",
    "lib",
    "json"
]

from . import lib
from .tracker import create_tracker

# 3) lazy import pattern (PEP 562: module-level __getattr__)
def __getattr__(name: str):
    """Lazily import submodules on attribute access (e.g. `physiocore.bridging`)."""
    if name in __all__:
        if name == "create_tracker":
            return create_tracker
        mod = _import_module(f"{__name__}.{name}")
        globals()[name] = mod
        return mod
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

def __dir__():
    return sorted(list(globals().keys()) + __all__)
