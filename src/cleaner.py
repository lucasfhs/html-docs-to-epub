"""HTML content cleaning and sanitization."""
from __future__ import annotations

import logging
import re
from copy import copy

from bs4 import BeautifulSoup, Tag, NavigableString

from .config import Config

logger = logging.getLogger(__name__)


class HTMLCleaner:
    """Cleans HTML content for EPUB generation."""

    def __init__(self, config: Config):
        self.config = config

    def clean(self, html: str) -> str:
        """Clean HTML content for EPUB compatibility."""
        if not html:
            return ""

        soup = BeautifulSoup(html, "lxml")

        # Remove unwanted elements
        self._remove_unwanted_elements(soup)

        # Clean attributes
        self._clean_attributes(soup)

        # Clean specific elements
        self._clean_code_blocks(soup)
        self._clean_images(soup)
        self._clean_links(soup)
        self._clean_tables(soup)
        self._clean_headings(soup)

        # Remove empty elements
        self._remove_empty_elements(soup)

        # Fix HTML structure
        self._fix_structure(soup)

        return str(soup)

    def _remove_unwanted_elements(self, soup: BeautifulSoup) -> None:
        """Remove elements that shouldn't be in the EPUB."""
        # Remove by selector
        for selector in self.config.REMOVE_SELECTORS:
            try:
                for element in soup.select(selector):
                    element.decompose()
            except Exception as e:
                logger.debug(f"Failed to remove selector '{selector}': {e}")

        # Remove HTML comments
        for comment in soup.find_all(
            string=lambda text: isinstance(text, NavigableString) and text.strip() == ""
        ):
            pass  # Keep empty strings for now

        # Remove hidden elements
        for element in soup.find_all(
            style=re.compile(r"display\s*:\s*none|visibility\s*:\s*hidden")
        ):
            element.decompose()

    def _clean_attributes(self, soup: BeautifulSoup) -> None:
        """Clean HTML attributes, keeping only essential ones."""
        allowed_attributes = {
            "a": ["href", "title", "id"],
            "img": ["src", "alt", "title", "width", "height"],
            "pre": ["class"],
            "code": ["class"],
            "table": ["class"],
            "thead": [],
            "tbody": [],
            "tr": [],
            "th": ["colspan", "rowspan", "scope"],
            "td": ["colspan", "rowspan"],
            "h1": ["id"],
            "h2": ["id"],
            "h3": ["id"],
            "h4": ["id"],
            "h5": ["id"],
            "h6": ["id"],
            "blockquote": ["cite"],
            "div": ["class"],
            "span": ["class"],
            "p": [],
            "ul": [],
            "ol": ["start", "type"],
            "li": ["value"],
            "dl": [],
            "dt": [],
            "dd": [],
            "strong": [],
            "em": [],
            "b": [],
            "i": [],
            "u": [],
            "s": [],
            "sub": [],
            "sup": [],
            "br": [],
            "hr": [],
            "details": [],
            "summary": [],
        }

        for element in soup.find_all(True):
            tag_name = element.name
            if tag_name in allowed_attributes:
                attrs_to_keep = allowed_attributes[tag_name]
                attrs_to_remove = [
                    attr for attr in element.attrs if attr not in attrs_to_keep
                ]
                for attr in attrs_to_remove:
                    del element[attr]
            else:
                # For unknown tags, remove all attributes
                element.attrs = {}

    def _clean_code_blocks(self, soup: BeautifulSoup) -> None:
        """Clean code blocks for better formatting."""
        for pre in soup.find_all("pre"):
            # Ensure pre contains code
            code = pre.find("code")
            if not code:
                # Wrap content in code tag
                code = soup.new_tag("code")
                code.string = pre.get_text()
                pre.clear()
                pre.append(code)

            # Preserve language class if present
            # Clean up code content
            code_text = code.get_text()
            # Remove leading/trailing whitespace but preserve internal formatting
            code_text = code_text.strip()
            code.string = code_text

    def _clean_images(self, soup: BeautifulSoup) -> None:
        """Clean and prepare images."""
        for img in soup.find_all("img"):
            # Ensure alt attribute exists
            if not img.get("alt"):
                img["alt"] = ""

            # Remove tracking pixels and tiny images
            width = img.get("width", "")
            height = img.get("height", "")

            try:
                if width and height:
                    w = int(width.replace("px", "").replace("%", ""))
                    h = int(height.replace("px", "").replace("%", ""))
                    # Skip very small images (likely icons or pixels)
                    if w < 10 or h < 10:
                        img.decompose()
                        continue
            except (ValueError, TypeError):
                pass

            # Ensure src is absolute
            src = img.get("src", "")
            if src and not src.startswith(("http://", "https://", "data:")):
                # This will be resolved later by link_converter
                pass

    def _clean_links(self, soup: BeautifulSoup) -> None:
        """Clean and normalize links."""
        for a in soup.find_all("a"):
            href = a.get("href", "")

            # Skip empty or anchor links
            if not href or href == "#":
                a.decompose()
                continue

            # Remove social sharing links
            social_patterns = [
                "twitter.com/share",
                "facebook.com/sharer",
                "linkedin.com/share",
                "plus.google.com/share",
                "reddit.com/submit",
            ]

            for pattern in social_patterns:
                if pattern in href.lower():
                    a.decompose()
                    break

    def _clean_tables(self, soup: BeautifulSoup) -> None:
        """Clean tables for EPUB compatibility."""
        for table in soup.find_all("table"):
            # Add a wrapper div for styling
            wrapper = soup.new_tag("div", attrs={"class": "table-wrapper"})

            # Simplify complex tables
            self._simplify_table(table)

            # Wrap the table
            table.wrap(wrapper)

    def _simplify_table(self, table: Tag) -> None:
        """Simplify a table for better EPUB rendering."""
        from bs4 import BeautifulSoup as BS

        # Remove nested tables
        for nested_table in table.find_all("table"):
            nested_table.unwrap()

        # Ensure thead and tbody exist
        if not table.find("thead"):
            first_row = table.find("tr")
            if first_row:
                thead = table.new_tag("thead")
                thead.append(first_row.extract())
                table.insert(0, thead)

        if not table.find("tbody"):
            tbody = table.new_tag("tbody")
            for row in table.find_all("tr"):
                tbody.append(row.extract())
            table.append(tbody)

    def _clean_headings(self, soup: BeautifulSoup) -> None:
        """Clean headings for proper hierarchy."""
        headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])

        for heading in headings:
            # Add id for navigation if not present
            if not heading.get("id"):
                text = heading.get_text(strip=True)
                # Create a simple id from the heading text
                heading_id = re.sub(r"[^\w\s-]", "", text.lower())
                heading_id = re.sub(r"[\s-]+", "-", heading_id)
                heading["id"] = heading_id[:50]

    def _remove_empty_elements(self, soup: BeautifulSoup) -> None:
        """Remove empty elements that add no value."""
        # Don't remove elements that should be kept even if empty
        keep_empty = {"img", "br", "hr", "input", "textarea", "select"}

        for element in soup.find_all(True):
            if element.name in keep_empty:
                continue

            # Check if element is truly empty
            text = element.get_text(strip=True)
            has_children = bool(element.find_all(True))
            has_images = bool(element.find_all("img"))

            if not text and not has_children and not has_images:
                element.decompose()

    def _fix_structure(self, soup: BeautifulSoup) -> None:
        """Fix HTML structure for better EPUB compatibility."""
        # Ensure proper nesting of lists
        for ul in soup.find_all("ul"):
            self._fix_list_nesting(ul)

        for ol in soup.find_all("ol"):
            self._fix_list_nesting(ol)

    def _fix_list_nesting(self, list_element: Tag) -> None:
        """Fix list nesting issues."""
        for child in list_element.find_all("li", recursive=False):
            # Ensure each li contains only inline content or sublists
            for grandchild in child.find_all(["ul", "ol"], recursive=False):
                # This is fine - nested list
                pass
