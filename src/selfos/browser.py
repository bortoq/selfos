"""
Browser Module for Self OS (Phase 3)

Provides quick access and navigation to web services.
This is a lightweight abstraction layer.
"""

from typing import Dict, Any
from datetime import datetime


class QuickLink:
    """Represents a quick link to a web service"""

    def __init__(self, name: str, url: str, category: str = "general"):
        self.name = name
        self.url = url
        self.category = category

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "url": self.url,
            "category": self.category
        }


class BrowserService:
    """
    Service for managing quick access to web services and navigation.
    """

    def __init__(self):
        self.links: Dict[str, QuickLink] = {}
        self._init_default_links()

    def _init_default_links(self):
        """Initialize common useful links"""
        defaults = [
            ("gmail", "https://mail.google.com", "email"),
            ("calendar", "https://calendar.google.com", "productivity"),
            ("notion", "https://www.notion.so", "productivity"),
            ("github", "https://github.com", "development"),
            ("todoist", "https://todoist.com", "productivity"),
        ]
        for name, url, category in defaults:
            self.add_link(name, url, category)

    def add_link(self, name: str, url: str, category: str = "general") -> QuickLink:
        """Add a new quick link"""
        link = QuickLink(name, url, category)
        self.links[name.lower()] = link
        return link

    def get_link(self, name: str) -> QuickLink | None:
        """Get a link by name"""
        return self.links.get(name.lower())

    def list_links(self, category: str = None) -> list[QuickLink]:
        """List all links, optionally filtered by category"""
        if category:
            return [link for link in self.links.values() if link.category == category]
        return list(self.links.values())

    def open_link(self, name: str) -> str:
        """Simulate opening a link (returns the URL)"""
        link = self.get_link(name)
        if link:
            print(f"[BROWSER] Opening: {link.url}")
            return link.url
        else:
            print(f"[BROWSER] Link '{name}' not found")
            return ""

    def search(self, query: str) -> str:
        """Simulate web search"""
        url = f"https://duckduckgo.com/?q={query.replace(' ', '+')}"
        print(f"[BROWSER] Searching for: {query}")
        return url