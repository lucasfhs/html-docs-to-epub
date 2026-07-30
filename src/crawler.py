"""Web crawler for discovering documentation pages."""
from __future__ import annotations

import logging
import re
import time
from collections import deque
from urllib.parse import urlparse, urljoin

import httpx
from bs4 import BeautifulSoup

from .config import Config
from .models import Page, CrawlResult
from .utils import normalize_url, is_internal_url, is_docs_url, get_docs_prefix
from .sitemap import SitemapParser
from .cache import Cache
from .progress import ProgressTracker, console

logger = logging.getLogger(__name__)


class Crawler:
    """Crawls documentation sites to discover pages."""

    def __init__(self, config: Config, cache: Cache):
        self.config = config
        self.cache = cache
        self.visited: set[str] = set()
        self.queue: deque[tuple[str, int, str | None]] = deque()
        self.pages: list[Page] = []
        self.failed_urls: list[str] = []
        self.client = httpx.Client(
            timeout=config.timeout,
            follow_redirects=True,
            headers={"User-Agent": config.user_agent},
        )
        self.docs_prefix = get_docs_prefix(config.url)

    def crawl(self) -> CrawlResult:
        """Main crawling method that discovers all documentation pages."""
        logger.info(f"Starting crawl from {self.config.url}")

        # Phase 1: Discover URLs from sitemap
        sitemap_urls = self._discover_sitemap_urls()

        # Phase 2: Start crawling from initial URL
        self.queue.append((self.config.url, 0, None))

        progress = ProgressTracker()
        discovered_count = 0

        with progress.track("Discovering pages", self.config.max_pages) as p:
            while self.queue and len(self.pages) < self.config.max_pages:
                url, depth, parent_url = self.queue.popleft()

                normalized = normalize_url(url, self.config.url)
                if not normalized:
                    continue

                if normalized in self.visited:
                    continue

                if not self._should_visit(normalized):
                    continue

                self.visited.add(normalized)

                # Fetch and parse the page
                page = self._fetch_page(normalized, depth, parent_url)
                if page:
                    self.pages.append(page)
                    discovered_count += 1
                    p.update(p.tasks[0].id, completed=min(discovered_count, self.config.max_pages))

                    # Extract links from the page
                    if depth < 3:  # Limit depth
                        self._extract_links(page.html, normalized, depth)

                    # Respect rate limiting
                    time.sleep(self.config.delay)

        self.client.close()

        # Sort pages by order
        self.pages.sort(key=lambda p: p.order)

        return CrawlResult(
            pages=self.pages,
            failed_urls=self.failed_urls,
            discovered_urls=list(self.visited),
        )

    def _discover_sitemap_urls(self) -> list[str]:
        """Discover URLs from sitemaps."""
        sitemap_parser = SitemapParser(self.config)
        try:
            urls = sitemap_parser.discover_sitemap_urls(self.config.url)
            filtered = sitemap_parser.filter_urls(urls, self.config.url, self.docs_prefix)
            return filtered
        finally:
            sitemap_parser.close()

    def _should_visit(self, url: str) -> bool:
        """Determine if a URL should be visited."""
        config = Config()
        parsed = urlparse(url)

        # Check exclude patterns
        for pattern in config.EXCLUDE_PATTERNS:
            if pattern in url.lower():
                logger.debug(f"Excluding URL (pattern match): {url}")
                return False

        # Check include pattern if specified
        if self.config.include_pattern:
            if not re.search(self.config.include_pattern, url):
                logger.debug(f"Excluding URL (include pattern): {url}")
                return False

        # Check exclude pattern if specified
        if self.config.exclude_pattern:
            if re.search(self.config.exclude_pattern, url):
                logger.debug(f"Excluding URL (exclude pattern): {url}")
                return False

        # Check if it's an internal URL
        if not is_internal_url(url, self.config.url):
            logger.debug(f"Excluding URL (external): {url}")
            return False

        # Check if it's within documentation section
        if not is_docs_url(url, self.docs_prefix):
            logger.debug(f"Excluding URL (not in docs): {url}")
            return False

        return True

    def _fetch_page(
        self, url: str, depth: int, parent_url: str | None
    ) -> Page | None:
        """Fetch a single page and return a Page object."""
        try:
            response = self.client.get(url)
            response.raise_for_status()

            content_type = response.headers.get("content-type", "")
            if "html" not in content_type:
                logger.debug(f"Non-HTML content: {url}")
                return None

            html = response.text
            soup = BeautifulSoup(html, "lxml")

            # Extract title
            title = self._extract_title(soup, url)

            # Create page with order based on discovery
            order = len(self.pages) + 1
            filename = self._generate_filename(url, order)

            page = Page(
                url=url,
                title=title,
                html=html,
                depth=depth,
                order=order,
                parent_url=parent_url,
                local_filename=filename,
            )

            # Save to cache
            self.cache.save_page(page)

            logger.debug(f"Fetched: {url} (depth={depth})")
            return page

        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            if status == 404:
                logger.warning(f"Page not found (404): {url}")
            elif status == 403:
                logger.warning(f"Access denied (403): {url}")
            elif status == 429:
                logger.warning(f"Rate limited (429): {url}")
                time.sleep(5)  # Wait longer on rate limit
            else:
                logger.warning(f"HTTP {status} error for {url}")
            self.failed_urls.append(url)
            return None

        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            self.failed_urls.append(url)
            return None

    def _extract_title(self, soup: BeautifulSoup, url: str) -> str:
        """Extract the title from a page."""
        # Try h1 first
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)[:200]

        # Try title tag
        title_tag = soup.find("title")
        if title_tag:
            title_text = title_tag.get_text(strip=True)
            # Remove site name if present (usually after | or -)
            if " | " in title_text:
                title_text = title_text.split(" | ")[0]
            elif " - " in title_text:
                title_text = title_text.split(" - ")[0]
            return title_text[:200]

        # Fallback to URL
        from .utils import extract_title_from_url
        return extract_title_from_url(url)

    def _generate_filename(self, url: str, order: int) -> str:
        """Generate a filename for the page."""
        from .utils import sanitize_filename

        parsed = urlparse(url)
        path = parsed.path.rstrip("/")

        # Get the last meaningful part
        parts = [p for p in path.split("/") if p and p != "docs"]
        if parts:
            name = parts[-1]
        else:
            name = "index"

        sanitized = sanitize_filename(name)
        return f"{order:03d}-{sanitized}.xhtml"

    def _extract_links(self, html: str, base_url: str, current_depth: int) -> None:
        """Extract internal links from HTML and add to queue."""
        soup = BeautifulSoup(html, "lxml")

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
                continue

            # Resolve relative URL
            full_url = urljoin(base_url, href)
            normalized = normalize_url(full_url, self.config.url)

            if normalized and normalized not in self.visited:
                self.queue.append((normalized, current_depth + 1, base_url))
