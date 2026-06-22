"""
Self OS - Personal Operating System
Phase 4: Platform — Plugin Platform, Marketplace, Hooks, Delegation Rules
"""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _metadata_version

try:
    __version__ = _metadata_version("selfos")
except PackageNotFoundError:
    # fallback for development without install
    __version__ = "0.4.0"
