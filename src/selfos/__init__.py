"""
Self OS - Personal Operating System
Phase 5c: Integrations — Calendar, Todoist, GitHub, Multi-source Suggestions
"""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _metadata_version

try:
    __version__ = _metadata_version("selfos")
except PackageNotFoundError:
    # fallback for development without install
    __version__ = "0.7.0"
