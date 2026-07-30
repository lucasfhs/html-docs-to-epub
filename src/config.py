"""Configuration settings for the documentation to EPUB converter."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Config:
    """Main configuration for the conversion process."""

    url: str = ""
    output: str = ""
    title: str = ""
    author: str = ""
    max_pages: int = 500
    workers: int = 5
    delay: float = 0.3
    image_quality: int = 80
    max_image_width: int = 1200
    use_playwright: bool = False
    force: bool = False
    no_images: bool = False
    include_pattern: str = ""
    exclude_pattern: str = ""
    verbose: bool = False

    # Send to Kindle settings
    send_to_kindle: bool = False
    kindle_email: str = ""
    smtp_email: str = ""
    smtp_password: str = ""
    smtp_server: str = ""
    smtp_port: int = 587
    smtp_use_tls: bool = True

    user_agent: str = (
        "Mozilla/5.0 (compatible; DocToEPUB/1.0; +https://github.com/doc-to-epub)"
    )
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0

    cache_dir: Path = field(default_factory=lambda: Path(".cache"))
    output_dir: Path = field(default_factory=lambda: Path("output"))
    log_dir: Path = field(default_factory=lambda: Path("logs"))

    # URL normalization parameters to remove
    TRACKING_PARAMS: list[str] = field(
        default_factory=lambda: [
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "utm_term",
            "utm_content",
            "ref",
            "source",
            "fbclid",
            "gclid",
        ]
    )

    # URL patterns to exclude
    EXCLUDE_PATTERNS: list[str] = field(
        default_factory=lambda: [
            "/login",
            "/signin",
            "/signup",
            "/register",
            "/admin",
            "/wp-admin",
            "/logout",
            "/signout",
            "/edit",
            "/github.com",
            "/twitter.com",
            "/facebook.com",
            "/linkedin.com",
            "mailto:",
            "tel:",
            "javascript:",
            ".pdf",
            ".zip",
            ".tar.gz",
            ".mp4",
            ".mp3",
            ".exe",
            ".dmg",
        ]
    )

    # Content selectors to try for main content extraction
    CONTENT_SELECTORS: list[str] = field(
        default_factory=lambda: [
            "main",
            "article",
            '[role="main"]',
            ".content",
            ".documentation",
            ".docs-content",
            ".markdown-body",
            ".theme-doc-markdown",
            ".md-content",
            ".prose",
            ".doc-content",
            ".page-content",
            "#content",
            "#main-content",
            ".body-content",
            ".main-content",
        ]
    )

    # Elements to remove from content
    REMOVE_SELECTORS: list[str] = field(
        default_factory=lambda: [
            "header",
            "footer",
            "nav",
            ".sidebar",
            ".menu",
            ".navigation",
            ".breadcrumb",
            ".breadcrumbs",
            ".toc",
            ".table-of-contents",
            ".ad",
            ".advertisement",
            ".banner",
            ".popup",
            ".modal",
            ".newsletter",
            ".social",
            ".share",
            ".feedback",
            ".edit-this-page",
            ".page-nav",
            ".prev-next",
            'a[href*="edit"]',
            'a[href*="github.com"][href*="edit"]',
            "script",
            "style",
            "noscript",
            "iframe",
            "form",
            "button.social",
            ".cookie",
            ".announcement",
        ]
    )
