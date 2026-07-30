"""Data models for the documentation to EPUB converter."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Page:
    """Represents a documentation page."""

    url: str
    title: str = ""
    html: str = ""
    cleaned_html: str = ""
    depth: int = 0
    order: int = 0
    parent_url: str | None = None
    local_filename: str = ""
    images: list[str] = field(default_factory=list)
    success: bool = True
    error: str = ""


@dataclass
class ImageInfo:
    """Represents an image to be included in the EPUB."""

    url: str
    local_path: str = ""
    alt_text: str = ""
    width: int = 0
    height: int = 0
    format: str = "JPEG"
    success: bool = True


@dataclass
class CrawlResult:
    """Result of crawling a documentation site."""

    pages: list[Page] = field(default_factory=list)
    failed_urls: list[str] = field(default_factory=list)
    discovered_urls: list[str] = field(default_factory=list)


@dataclass
class Chapter:
    """Represents a chapter in the EPUB."""

    title: str
    filename: str
    content: str
    level: int = 1
    subchapters: list[Chapter] = field(default_factory=list)
    page_url: str = ""


@dataclass
class BookMetadata:
    """Metadata for the generated EPUB."""

    title: str = ""
    author: str = ""
    description: str = ""
    language: str = "pt-BR"
    source_url: str = ""
    generation_date: str = ""
    generator: str = "Documentation to EPUB Converter"
