"""Link conversion for internal EPUB links."""
from __future__ import annotations

import logging
from urllib.parse import urlparse, urljoin

from bs4 import BeautifulSoup

from .models import Page
from .utils import normalize_url, sanitize_filename

logger = logging.getLogger(__name__)


class LinkConverter:
    """Converts internal documentation links to EPUB internal links."""

    def __init__(self, pages: list[Page]):
        self.pages = pages
        self.url_to_filename: dict[str, str] = {}
        self._build_mapping()

    def _build_mapping(self) -> None:
        """Build a mapping from URLs to filenames."""
        for page in self.pages:
            self.url_to_filename[page.url] = page.local_filename

    def convert_links(self, html: str, current_page: Page) -> str:
        """Convert all internal links in HTML to EPUB links."""
        soup = BeautifulSoup(html, "lxml")

        for a in soup.find_all("a", href=True):
            href = a["href"]

            # Skip anchors and external links
            if href.startswith(("#", "javascript:", "mailto:", "tel:")):
                continue

            # Resolve relative URL
            if not href.startswith(("http://", "https://")):
                absolute_url = urljoin(current_page.url, href)
            else:
                absolute_url = href

            # Normalize the URL
            normalized = normalize_url(absolute_url)

            # Check if this is an internal link
            if normalized in self.url_to_filename:
                # Convert to internal link
                filename = self.url_to_filename[normalized]

                # Handle anchors within the same page
                if "#" in href:
                    anchor = href.split("#", 1)[1]
                    a["href"] = f"{filename}#{anchor}"
                else:
                    a["href"] = filename

                logger.debug(f"Converted link: {href} -> {a['href']}")
            else:
                # Keep external links as-is
                # But ensure they have the full URL
                if not href.startswith(("http://", "https://")):
                    a["href"] = absolute_url

        return str(soup)

    def get_internal_links(self, html: str, base_url: str) -> list[str]:
        """Extract internal links from HTML."""
        soup = BeautifulSoup(html, "lxml")
        internal_links = []

        for a in soup.find_all("a", href=True):
            href = a["href"]

            # Skip anchors and non-HTTP links
            if href.startswith(("#", "javascript:", "mailto:", "tel:")):
                continue

            # Resolve relative URL
            if not href.startswith(("http://", "https://")):
                absolute_url = urljoin(base_url, href)
            else:
                absolute_url = href

            # Normalize
            normalized = normalize_url(absolute_url)

            # Check if it's an internal page
            if normalized in self.url_to_filename:
                internal_links.append(normalized)

        return internal_links
