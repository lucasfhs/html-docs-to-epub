"""Sitemap parsing and URL discovery."""
from __future__ import annotations

import logging
from urllib.parse import urlparse
from xml.etree import ElementTree

import httpx

from .config import Config
from .utils import normalize_url

logger = logging.getLogger(__name__)


class SitemapParser:
    """Parses XML sitemaps to discover documentation URLs."""

    def __init__(self, config: Config):
        self.config = config
        self.client = httpx.Client(
            timeout=config.timeout,
            follow_redirects=True,
            headers={"User-Agent": config.user_agent},
        )

    def discover_sitemap_urls(self, base_url: str) -> list[str]:
        """Discover and parse sitemaps for the given URL."""
        urls = []

        # Try common sitemap locations
        sitemap_locations = [
            "/sitemap.xml",
            "/sitemap_index.xml",
            "/sitemap-index.xml",
            "/sitemaps.xml",
        ]

        parsed = urlparse(base_url)
        base = f"{parsed.scheme}://{parsed.netloc}"

        for location in sitemap_locations:
            sitemap_url = base + location
            try:
                found_urls = self._parse_sitemap(sitemap_url)
                urls.extend(found_urls)
                if found_urls:
                    logger.info(f"Found {len(found_urls)} URLs in {sitemap_url}")
            except Exception as e:
                logger.debug(f"Could not parse {sitemap_url}: {e}")

        return list(set(urls))

    def _parse_sitemap(self, url: str) -> list[str]:
        """Parse a single sitemap XML file."""
        try:
            response = self.client.get(url)
            response.raise_for_status()
        except httpx.HTTPError as e:
            logger.debug(f"Error fetching sitemap {url}: {e}")
            return []

        content_type = response.headers.get("content-type", "")
        if "xml" not in content_type and "text" not in content_type:
            logger.debug(f"Non-XML content type for sitemap: {content_type}")
            return []

        try:
            root = ElementTree.fromstring(response.content)
        except ElementTree.ParseError as e:
            logger.debug(f"Error parsing sitemap XML: {e}")
            return []

        urls = []

        # Handle sitemap index (contains other sitemaps)
        ns = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        sitemaps = root.findall(".//ns:sitemap/ns:loc", ns)
        if sitemaps:
            for sitemap_loc in sitemaps:
                if sitemap_loc.text:
                    sub_urls = self._parse_sitemap(sitemap_loc.text.strip())
                    urls.extend(sub_urls)
            return urls

        # Handle regular sitemap (contains URLs)
        for url_elem in root.findall(".//ns:url/ns:loc", ns):
            if url_elem.text:
                url_text = url_elem.text.strip()
                normalized = normalize_url(url_text, url)
                if normalized:
                    urls.append(normalized)

        return urls

    def filter_urls(
        self, urls: list[str], base_url: str, docs_prefix: str
    ) -> list[str]:
        """Filter URLs to keep only those within the documentation section."""
        from .utils import is_internal_url, is_docs_url

        filtered = []
        for url in urls:
            if is_internal_url(url, base_url) and is_docs_url(url, docs_prefix):
                filtered.append(url)

        return list(set(filtered))

    def close(self) -> None:
        """Close the HTTP client."""
        self.client.close()
