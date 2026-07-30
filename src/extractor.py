"""Content extraction from HTML pages."""
from __future__ import annotations

import logging
from typing import Optional

from bs4 import BeautifulSoup, Tag

from .config import Config

logger = logging.getLogger(__name__)


class ContentExtractor:
    """Extracts main content from HTML pages."""

    def __init__(self, config: Config):
        self.config = config

    def extract(self, html: str, url: str = "") -> str:
        """Extract the main content from HTML."""
        if not html:
            return ""

        soup = BeautifulSoup(html, "lxml")

        # Remove scripts and styles first
        for element in soup(["script", "style", "noscript"]):
            element.decompose()

        # Try to find main content using selectors
        content = self._find_main_content(soup)

        if content:
            return str(content)

        # Fallback: use readability-like heuristic
        return self._heuristic_extraction(soup)

    def _find_main_content(self, soup: BeautifulSoup) -> Optional[Tag]:
        """Try to find main content using CSS selectors."""
        for selector in self.config.CONTENT_SELECTORS:
            try:
                elements = soup.select(selector)
                if elements:
                    # Use the first matching element with substantial content
                    for elem in elements:
                        text_length = len(elem.get_text(strip=True))
                        if text_length > 200:  # Minimum content threshold
                            logger.debug(
                                f"Found content with selector '{selector}' "
                                f"({text_length} chars)"
                            )
                            return elem
            except Exception as e:
                logger.debug(f"Selector '{selector}' failed: {e}")

        return None

    def _heuristic_extraction(self, soup: BeautifulSoup) -> str:
        """Extract content using heuristics based on text density."""
        # Find all potential content containers
        candidates = []

        for tag in soup.find_all(["div", "section", "article", "main"]):
            score = self._calculate_content_score(tag)
            if score > 0:
                candidates.append((tag, score))

        if not candidates:
            # Fall back to body
            body = soup.find("body")
            if body:
                return self._clean_element(body)
            return str(soup)

        # Sort by score and use the best candidate
        candidates.sort(key=lambda x: x[1], reverse=True)
        best = candidates[0][0]

        return self._clean_element(best)

    def _calculate_content_score(self, element: Tag) -> float:
        """Calculate a score for an element based on content indicators."""
        score = 0.0

        # Count text
        text = element.get_text(strip=True)
        text_length = len(text)

        # Count paragraphs
        paragraphs = element.find_all("p")
        score += len(paragraphs) * 3

        # Count headings
        headings = element.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
        score += len(headings) * 5

        # Count code blocks
        code_blocks = element.find_all("pre")
        score += len(code_blocks) * 4

        # Count lists
        lists = element.find_all(["ul", "ol"])
        score += len(lists) * 2

        # Count links (but not too many - could be navigation)
        links = element.find_all("a")
        if len(links) < 50:
            score += len(links) * 1

        # Penalize elements with many links (likely navigation)
        if len(links) > 50:
            score -= 20

        # Penalize elements with short text
        if text_length < 100:
            score -= 50

        # Bonus for elements with longer text
        if text_length > 500:
            score += 10
        if text_length > 1000:
            score += 10

        # Check for negative indicators
        class_attr = element.get("class", [])
        id_attr = element.get("id", "")

        negative_patterns = [
            "nav", "menu", "sidebar", "footer", "header",
            "breadcrumb", "toc", "table-of-contents", "pagination",
            "share", "social", "comment", "advertisement", "ad",
        ]

        for pattern in negative_patterns:
            if pattern in " ".join(class_attr).lower():
                score -= 30
            if pattern in id_attr.lower():
                score -= 30

        return score

    def _clean_element(self, element: Tag) -> str:
        """Clean an HTML element by removing unwanted parts."""
        # Create a copy to avoid modifying the original
        from copy import copy
        cleaned = copy(element)

        # Remove unwanted elements
        for selector in self.config.REMOVE_SELECTORS:
            try:
                for unwanted in cleaned.select(selector):
                    unwanted.decompose()
            except Exception as e:
                logger.debug(f"Failed to remove selector '{selector}': {e}")

        # Remove empty elements
        self._remove_empty_elements(cleaned)

        return str(cleaned)

    def _remove_empty_elements(self, element: Tag) -> None:
        """Recursively remove empty elements."""
        if not isinstance(element, Tag):
            return

        children_to_remove = []
        for child in element.children:
            if isinstance(child, Tag):
                self._remove_empty_elements(child)
                if not child.get_text(strip=True) and not child.find(["img", "video", "audio", "iframe"]):
                    children_to_remove.append(child)

        for child in children_to_remove:
            child.decompose()

    def extract_table_of_contents(self, html: str) -> list[dict]:
        """Extract a table of contents from headings in the HTML."""
        soup = BeautifulSoup(html, "lxml")
        toc = []

        for heading in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
            level = int(heading.name[1])
            text = heading.get_text(strip=True)
            if text:
                toc.append({"level": level, "text": text})

        return toc
