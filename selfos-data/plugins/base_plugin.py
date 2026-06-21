"""
Base Plugin Interface for Self OS

All external service plugins must inherit from this class.
"""

from abc import ABC, abstractmethod
from typing import Any


class BasePlugin(ABC):
    """
    Abstract base class for all Self OS plugins.

    Each plugin is responsible for fetching data from an external service
    and (optionally) pushing data back.
    """

    name: str = "base"
    description: str = "Base plugin"

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}

    @abstractmethod
    def fetch(self) -> list[dict[str, Any]]:
        """
        Fetch new events/activities from the external service.

        Returns:
            List of standardized event dictionaries.
        """
        pass

    def push(self, event: dict[str, Any]) -> bool:
        """
        Push an event back to the external service (optional).

        Returns:
            True if successful, False otherwise.
        """
        # Default implementation does nothing
        return False

    def validate_config(self) -> bool:
        """Check if required configuration is present."""
        return True

    def __str__(self):
        return f"{self.name} Plugin"
