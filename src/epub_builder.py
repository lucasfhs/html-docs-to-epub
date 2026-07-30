"""EPUB generation using ebooklib."""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

from .config import Config
from .models import Chapter, BookMetadata, Page

logger = logging.getLogger(__name__)


class EPUBBuilder:
    """Builds EPUB files from chapters and metadata."""

    def __init__(self, config: Config):
        self.config = config
        self.book = epub.EpubBook()

    def build(
        self,
        chapters: list[Chapter],
        metadata: BookMetadata,
        images_dir: Path,
        css_path: Path,
    ) -> epub.EpubBook:
        """Build the complete EPUB book."""
        # Set metadata
        self._set_metadata(metadata)

        # Add CSS
        self._add_css(css_path)

        # Add cover page
        self._add_cover_page(metadata)

        # Add title page
        self._add_title_page(metadata)

        # Add chapters
        epub_chapters = []
        for chapter in chapters:
            epub_chapter = self._add_chapter(chapter)
            epub_chapters.append(epub_chapter)

        # Add images
        self._add_images(images_dir)

        # Add table of contents
        self._add_toc(epub_chapters)

        # Set spine
        self._set_spine(epub_chapters)

        # Add final page
        self._add_final_page(metadata)

        return self.book

    def _set_metadata(self, metadata: BookMetadata) -> None:
        """Set book metadata."""
        self.book.set_identifier(
            f"doc-to-epub-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )
        self.book.set_title(metadata.title)
        self.book.set_language(metadata.language)
        self.book.add_author(metadata.author)

        # Add additional metadata
        self.book.add_metadata(
            "DC",
            "description",
            f"Documentation converted from {metadata.source_url}",
        )
        self.book.add_metadata("DC", "date", metadata.generation_date)
        self.book.add_metadata("DC", "source", metadata.source_url)
        self.book.add_metadata("DC", "generator", metadata.generator)

    def _add_css(self, css_path: Path) -> None:
        """Add CSS stylesheet to the book."""
        if css_path.exists():
            css_content = css_path.read_text(encoding="utf-8")
        else:
            css_content = self._get_default_css()

        css_item = epub.EpubItem(
            uid="style",
            file_name="style/default.css",
            media_type="text/css",
            content=css_content.encode("utf-8"),
        )
        self.book.add_item(css_item)
        self.css_item = css_item

    def _get_default_css(self) -> str:
        """Return default CSS if no file is provided."""
        return """
body {
    font-family: serif;
    line-height: 1.6;
    margin: 1em;
    text-align: justify;
}

h1, h2, h3, h4, h5, h6 {
    page-break-after: avoid;
    margin-top: 1.5em;
    margin-bottom: 0.5em;
}

h1 { font-size: 1.8em; }
h2 { font-size: 1.5em; }
h3 { font-size: 1.3em; }
h4 { font-size: 1.1em; }

p {
    margin: 0.5em 0;
    orphans: 3;
    widows: 3;
}

a {
    color: #1a73e8;
    text-decoration: none;
}

img {
    display: block;
    max-width: 100%;
    height: auto;
    margin: 1em auto;
}

pre {
    background-color: #f5f5f5;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 0.8em;
    overflow-x: auto;
    font-size: 0.85em;
    line-height: 1.4;
    page-break-inside: avoid;
}

code {
    font-family: monospace;
    background-color: #f5f5f5;
    padding: 0.1em 0.3em;
    border-radius: 3px;
    font-size: 0.9em;
}

pre code {
    background-color: transparent;
    padding: 0;
    border-radius: 0;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 1em 0;
    font-size: 0.9em;
    page-break-inside: avoid;
}

th, td {
    border: 1px solid #ddd;
    padding: 0.5em;
    text-align: left;
    word-wrap: break-word;
}

th {
    background-color: #f5f5f5;
    font-weight: bold;
}

.table-wrapper {
    overflow-x: auto;
}

blockquote {
    border-left: 4px solid #ddd;
    margin: 1em 0;
    padding: 0.5em 1em;
    color: #666;
    background-color: #fafafa;
}

ul, ol {
    margin: 0.5em 0;
    padding-left: 2em;
}

li {
    margin: 0.3em 0;
}

.note, .tip, .warning, .alert, .important {
    padding: 1em;
    margin: 1em 0;
    border-radius: 4px;
    border-left: 4px solid;
}

.note { background-color: #e3f2fd; border-color: #2196f3; }
.tip { background-color: #e8f5e9; border-color: #4caf50; }
.warning { background-color: #fff3e0; border-color: #ff9800; }
.alert, .important { background-color: #ffebee; border-color: #f44336; }

.cover {
    text-align: center;
    padding: 2em;
}

.cover h1 {
    font-size: 2em;
    margin-top: 2em;
}

.title-page {
    text-align: center;
    padding: 3em 1em;
}

.title-page h1 {
    font-size: 2.5em;
    margin-bottom: 1em;
}

.title-page .author {
    font-size: 1.2em;
    color: #666;
}

.title-page .date {
    font-size: 1em;
    color: #999;
    margin-top: 2em;
}

.toc {
    padding: 1em;
}

.toc h1 {
    text-align: center;
    margin-bottom: 2em;
}

.toc ul {
    list-style: none;
    padding-left: 0;
}

.toc li {
    margin: 0.5em 0;
}

.toc li.level-2 {
    padding-left: 1.5em;
}

.toc li.level-3 {
    padding-left: 3em;
}

.final-page {
    text-align: center;
    padding: 3em 1em;
    color: #666;
    font-style: italic;
}

hr {
    border: none;
    border-top: 1px solid #ddd;
    margin: 2em 0;
}
"""

    def _add_cover_page(self, metadata: BookMetadata) -> None:
        """Add a simple cover page."""
        cover_html = f"""
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>Cover</title>
    <link rel="stylesheet" href="style/default.css" type="text/css"/>
</head>
<body>
    <div class="cover">
        <h1>{self._escape_html(metadata.title)}</h1>
        <p>{self._escape_html(metadata.author)}</p>
    </div>
</body>
</html>
"""
        cover = epub.EpubHtml(
            title="Cover",
            file_name="cover.xhtml",
            lang=metadata.language,
            content=cover_html.encode("utf-8"),
        )
        cover.add_item(self.css_item)
        self.book.add_item(cover)
        self.cover = cover

    def _add_title_page(self, metadata: BookMetadata) -> None:
        """Add a title page with generation information."""
        title_html = f"""
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>Title Page</title>
    <link rel="stylesheet" href="style/default.css" type="text/css"/>
</head>
<body>
    <div class="title-page">
        <h1>{self._escape_html(metadata.title)}</h1>
        <p class="author">{self._escape_html(metadata.author)}</p>
        <p class="date">Generated on: {metadata.generation_date}</p>
        <p class="source">Source: {self._escape_html(metadata.source_url)}</p>
    </div>
</body>
</html>
"""
        title_page = epub.EpubHtml(
            title="Title Page",
            file_name="title.xhtml",
            lang=metadata.language,
            content=title_html.encode("utf-8"),
        )
        title_page.add_item(self.css_item)
        self.book.add_item(title_page)
        self.title_page = title_page

    def _add_chapter(self, chapter: Chapter) -> epub.EpubHtml:
        """Add a chapter to the book."""
        chapter_html = f"""
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>{self._escape_html(chapter.title)}</title>
    <link rel="stylesheet" href="style/default.css" type="text/css"/>
</head>
<body>
    <h1>{self._escape_html(chapter.title)}</h1>
    {chapter.content}
</body>
</html>
"""
        epub_chapter = epub.EpubHtml(
            title=chapter.title,
            file_name=chapter.filename,
            lang="pt-BR",
            content=chapter_html.encode("utf-8"),
        )
        epub_chapter.add_item(self.css_item)
        self.book.add_item(epub_chapter)

        return epub_chapter

    def _add_images(self, images_dir: Path) -> None:
        """Add images to the book."""
        if not images_dir.exists():
            return

        for image_file in images_dir.glob("*"):
            if image_file.suffix.lower() in (".jpg", ".jpeg", ".png", ".gif", ".webp"):
                try:
                    media_type = self._get_media_type(image_file.suffix)
                    with open(image_file, "rb") as f:
                        image_data = f.read()

                    image = epub.EpubItem(
                        uid=f"img-{image_file.stem}",
                        file_name=f"images/{image_file.name}",
                        media_type=media_type,
                        content=image_data,
                    )
                    self.book.add_item(image)
                except Exception as e:
                    logger.warning(f"Failed to add image {image_file}: {e}")

    def _get_media_type(self, extension: str) -> str:
        """Get MIME type for an image extension."""
        media_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        return media_types.get(extension.lower(), "image/jpeg")

    def _add_toc(self, chapters: list[epub.EpubHtml]) -> None:
        """Add table of contents."""
        # Create NCX navigation
        self.book.toc = [
            (epub.Link(chapter.file_name, chapter.title, chapter.file_name.split(".")[0]))
            for chapter in chapters
        ]

        # Add default NCX and Navigation documents
        self.book.add_item(epub.EpubNcx())
        self.book.add_item(epub.EpubNav())

    def _set_spine(self, chapters: list[epub.EpubHtml]) -> None:
        """Set the book spine (reading order)."""
        spine_items = ["nav", self.cover, self.title_page]
        spine_items.extend(chapters)
        self.book.spine = spine_items

    def _add_final_page(self, metadata: BookMetadata) -> None:
        """Add a final page with source information."""
        final_html = f"""
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>End</title>
    <link rel="stylesheet" href="style/default.css" type="text/css"/>
</head>
<body>
    <div class="final-page">
        <hr/>
        <p>This book was generated from the documentation at:</p>
        <p><a href="{self._escape_html(metadata.source_url)}">{self._escape_html(metadata.source_url)}</a></p>
        <p>Generated on: {metadata.generation_date}</p>
        <p>Generator: {self._escape_html(metadata.generator)}</p>
    </div>
</body>
</html>
"""
        final_page = epub.EpubHtml(
            title="End",
            file_name="final.xhtml",
            lang=metadata.language,
            content=final_html.encode("utf-8"),
        )
        final_page.add_item(self.css_item)
        self.book.add_item(final_page)

    def _escape_html(self, text: str) -> str:
        """Escape special HTML characters."""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
        )

    def save(self, output_path: Path) -> None:
        """Save the EPUB to a file."""
        epub.write_epub(str(output_path), self.book, {})
        logger.info(f"EPUB saved to {output_path}")
