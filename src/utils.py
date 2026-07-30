"""Utility functions for URL handling and text processing."""
from __future__ import annotations

import hashlib
import logging
import re
from pathlib import Path
from urllib.parse import urlparse, urljoin, urlunparse, parse_qs, urlencode

from .config import Config

logger = logging.getLogger(__name__)


def normalize_url(url: str, base_url: str = "") -> str:
    """Normalize a URL by removing tracking parameters and fragments."""
    if not url:
        return ""

    # Resolve relative URLs
    if base_url and not url.startswith(("http://", "https://")):
        url = urljoin(base_url, url)

    parsed = urlparse(url)

    # Skip non-HTTP schemes
    if parsed.scheme not in ("http", "https"):
        return ""

    # Remove tracking parameters
    query_params = parse_qs(parsed.query, keep_blank_values=False)
    config = Config()
    cleaned_params = {
        k: v for k, v in query_params.items() if k not in config.TRACKING_PARAMS
    }

    # Rebuild URL without fragments and with cleaned params
    cleaned_query = urlencode(cleaned_params, doseq=True) if cleaned_params else ""

    normalized = urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path.rstrip("/") or "/",
            parsed.params,
            cleaned_query,
            "",  # Remove fragment
        )
    )

    return normalized


def is_internal_url(url: str, base_url: str) -> bool:
    """Check if a URL belongs to the same domain as the base URL."""
    if not url or not base_url:
        return False

    parsed_url = urlparse(url)
    parsed_base = urlparse(base_url)

    return parsed_url.netloc == parsed_base.netloc


def is_docs_url(url: str, docs_prefix: str) -> bool:
    """Check if a URL is within the documentation section."""
    if not url or not docs_prefix:
        return True

    parsed = urlparse(url)
    path = parsed.path.rstrip("/")

    # Check if the URL path starts with the docs prefix
    return path.startswith(docs_prefix.rstrip("/"))


def get_docs_prefix(url: str) -> str:
    """Extract the documentation prefix from a URL."""
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")

    # Try to find a reasonable prefix
    # For example: /docs/hermes/ -> /docs/hermes
    parts = path.split("/")

    # If the URL ends with a slash, use the path as-is
    if path.endswith("/"):
        return path

    # Otherwise, use the full path
    return path


def sanitize_filename(name: str) -> str:
    """Convert a string to a safe filename."""
    # Remove or replace invalid characters
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    name = re.sub(r"_+", "_", name)
    name = re.sub(r"\s+", "-", name)
    name = re.sub(r"-+", "-", name)
    name = name.strip("-_.")

    # Limit length
    if len(name) > 100:
        name = name[:100]

    return name.lower() or "unnamed"


def generate_content_hash(content: str) -> str:
    """Generate a hash for content caching."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


def extract_title_from_url(url: str) -> str:
    """Extract a readable title from a URL path."""
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")

    # Get the last part of the path
    parts = path.split("/")
    last_part = parts[-1] if parts else ""

    if not last_part or last_part == "/":
        return "Index"

    # Convert hyphens and underscores to spaces
    title = last_part.replace("-", " ").replace("_", " ")

    # Capitalize words
    title = " ".join(word.capitalize() for word in title.split())

    return title or "Untitled"


def resolve_image_url(src: str, page_url: str) -> str:
    """Resolve an image URL relative to the page URL."""
    if not src:
        return ""

    # Handle data URIs
    if src.startswith("data:"):
        return src

    # Handle protocol-relative URLs
    if src.startswith("//"):
        parsed_page = urlparse(page_url)
        return f"{parsed_page.scheme}:{src}"

    # Resolve relative URLs
    return urljoin(page_url, src)


def get_file_extension(url: str) -> str:
    """Extract file extension from URL."""
    parsed = urlparse(url)
    path = parsed.path

    # Get the last part after splitting by /
    filename = path.split("/")[-1] if path else ""

    # Get extension
    if "." in filename:
        ext = filename.split(".")[-1].lower()
        # Limit to common image extensions
        if ext in ("jpg", "jpeg", "png", "gif", "webp", "svg", "bmp"):
            return ext

    return ""


def is_valid_image_url(url: str) -> bool:
    """Check if a URL points to a valid image."""
    if not url:
        return False

    # Skip data URIs (they're valid)
    if url.startswith("data:"):
        return True

    ext = get_file_extension(url)
    return ext in ("jpg", "jpeg", "png", "gif", "webp", "svg", "bmp")


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to a maximum length with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def get_domain(url: str) -> str:
    """Extract the domain from a URL."""
    parsed = urlparse(url)
    return parsed.netloc
