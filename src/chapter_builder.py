"""Chapter building from processed pages."""
from __future__ import annotations

import logging
import re
from pathlib import Path

from bs4 import BeautifulSoup

from .config import Config
from .models import Page, Chapter
from .cleaner import HTMLCleaner
from .extractor import ContentExtractor
from .link_converter import LinkConverter
from .image_processor import ImageProcessor

logger = logging.getLogger(__name__)


class ChapterBuilder:
    """Builds EPUB chapters from processed pages."""

    def __init__(self, config: Config):
        self.config = config
        self.cleaner = HTMLCleaner(config)
        self.extractor = ContentExtractor(config)

    def build_chapters(
        self,
        pages: list[Page],
        images_dir: Path,
        image_processor: ImageProcessor | None = None,
    ) -> list[Chapter]:
        """Build chapters from a list of pages."""
        chapters = []

        # Sort pages by order
        sorted_pages = sorted(pages, key=lambda p: p.order)

        # Create link converter for internal link conversion
        link_converter = LinkConverter(sorted_pages)

        for page in sorted_pages:
            if not page.success or not page.html:
                continue

            # Extract content
            content_html = self.extractor.extract(page.html, page.url)

            # Clean the content
            cleaned_html = self.cleaner.clean(content_html)

            # Process images if image processor is provided
            if image_processor and not self.config.no_images:
                cleaned_html, images = image_processor.process_images(
                    cleaned_html, page.url, images_dir
                )
                page.images = [img.local_path for img in images if img.success]

            # Convert internal links
            cleaned_html = link_converter.convert_links(cleaned_html, page)

            # Create chapter
            chapter = Chapter(
                title=page.title,
                filename=page.local_filename,
                content=cleaned_html,
                level=1,
                page_url=page.url,
            )

            # Extract subchapters from headings
            chapter.subchapters = self._extract_subchapters(
                cleaned_html, page.local_filename
            )

            chapters.append(chapter)
            logger.debug(f"Built chapter: {page.title}")

        return chapters

    def _extract_subchapters(self, html: str, base_filename: str) -> list[Chapter]:
        """Extract subchapters from headings in the content."""
        soup = BeautifulSoup(html, "lxml")
        subchapters = []

        # Find all headings
        headings = soup.find_all(["h2", "h3", "h4"])

        for i, heading in enumerate(headings):
            level = int(heading.name[1])
            title = heading.get_text(strip=True)

            if not title:
                continue

            # Create a filename for the subchapter anchor
            anchor_id = heading.get("id", "")
            if not anchor_id:
                # Generate anchor ID from title
                anchor_id = re.sub(r"[^\w\s-]", "", title.lower())
                anchor_id = re.sub(r"[\s-]+", "-", anchor_id)[:50]
                heading["id"] = anchor_id

            subchapter = Chapter(
                title=title,
                filename=f"{base_filename}#{anchor_id}",
                content="",
                level=level,
            )
            subchapters.append(subchapter)

        return subchapters

    def get_toc_from_chapters(self, chapters: list[Chapter]) -> list[dict]:
        """Generate a table of contents structure from chapters."""
        toc = []

        for chapter in chapters:
            toc_entry = {
                "title": chapter.title,
                "filename": chapter.filename,
                "level": 1,
            }

            # Add subchapters
            if chapter.subchapters:
                toc_entry["children"] = []
                for sub in chapter.subchapters:
                    toc_entry["children"].append({
                        "title": sub.title,
                        "filename": sub.filename,
                        "level": sub.level,
                    })

            toc.append(toc_entry)

        return toc
