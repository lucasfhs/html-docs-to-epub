"""Cache management for pages and images."""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from .config import Config
from .models import Page

logger = logging.getLogger(__name__)


class Cache:
    """Manages caching of pages and images for resume capability."""

    def __init__(self, config: Config, project_name: str = ""):
        self.config = config
        self.project_name = project_name or self._generate_project_name()
        self.cache_dir = config.cache_dir / self.project_name
        self.pages_dir = self.cache_dir / "pages"
        self.images_dir = self.cache_dir / "images"
        self.metadata_file = self.cache_dir / "metadata.json"
        self._ensure_dirs()

    def _generate_project_name(self) -> str:
        """Generate a project name from the URL."""
        from urllib.parse import urlparse

        parsed = urlparse(self.config.url)
        name = parsed.netloc.replace(".", "-")
        path_parts = [p for p in parsed.path.split("/") if p]
        if path_parts:
            name += "-" + "-".join(path_parts[:3])
        return name

    def _ensure_dirs(self) -> None:
        """Ensure cache directories exist."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.pages_dir.mkdir(exist_ok=True)
        self.images_dir.mkdir(exist_ok=True)

    def has_incomplete_process(self) -> bool:
        """Check if there's an incomplete processing session."""
        if not self.metadata_file.exists():
            return False

        metadata = self._load_metadata()
        return metadata.get("status") == "in_progress"

    def _load_metadata(self) -> dict:
        """Load metadata from cache."""
        if not self.metadata_file.exists():
            return {}
        try:
            with open(self.metadata_file, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def _save_metadata(self, metadata: dict) -> None:
        """Save metadata to cache."""
        with open(self.metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

    def start_session(self) -> None:
        """Mark the start of a processing session."""
        metadata = self._load_metadata()
        metadata["status"] = "in_progress"
        metadata["start_time"] = datetime.now().isoformat()
        metadata["url"] = self.config.url
        self._save_metadata(metadata)

    def complete_session(self, stats: dict | None = None) -> None:
        """Mark the completion of a processing session."""
        metadata = self._load_metadata()
        metadata["status"] = "completed"
        metadata["end_time"] = datetime.now().isoformat()
        if stats:
            metadata["stats"] = stats
        self._save_metadata(metadata)

    def save_page(self, page: Page) -> None:
        """Save a page to cache."""
        from .utils import sanitize_filename

        filename = sanitize_filename(page.url) + ".json"
        filepath = self.pages_dir / filename

        data = {
            "url": page.url,
            "title": page.title,
            "html": page.html,
            "cleaned_html": page.cleaned_html,
            "depth": page.depth,
            "order": page.order,
            "parent_url": page.parent_url,
            "local_filename": page.local_filename,
            "images": page.images,
            "success": page.success,
            "error": page.error,
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_page(self, url: str) -> Page | None:
        """Load a page from cache."""
        from .utils import sanitize_filename

        filename = sanitize_filename(url) + ".json"
        filepath = self.pages_dir / filename

        if not filepath.exists():
            return None

        try:
            with open(filepath, encoding="utf-8") as f:
                data = json.load(f)
            return Page(
                url=data["url"],
                title=data.get("title", ""),
                html=data.get("html", ""),
                cleaned_html=data.get("cleaned_html", ""),
                depth=data.get("depth", 0),
                order=data.get("order", 0),
                parent_url=data.get("parent_url"),
                local_filename=data.get("local_filename", ""),
                images=data.get("images", []),
                success=data.get("success", True),
                error=data.get("error", ""),
            )
        except (json.JSONDecodeError, IOError, KeyError):
            return None

    def page_exists(self, url: str) -> bool:
        """Check if a page exists in cache."""
        from .utils import sanitize_filename

        filename = sanitize_filename(url) + ".json"
        return (self.pages_dir / filename).exists()

    def save_image(self, url: str, local_path: str) -> None:
        """Save image metadata to cache."""
        from .utils import sanitize_filename

        filename = sanitize_filename(url) + ".json"
        filepath = self.images_dir / filename

        data = {"url": url, "local_path": local_path}

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_cached_image_path(self, url: str) -> str | None:
        """Get the local path for a cached image."""
        from .utils import sanitize_filename

        filename = sanitize_filename(url) + ".json"
        filepath = self.images_dir / filename

        if not filepath.exists():
            return None

        try:
            with open(filepath, encoding="utf-8") as f:
                data = json.load(f)
            local_path = data.get("local_path", "")
            if local_path and Path(local_path).exists():
                return local_path
        except (json.JSONDecodeError, IOError):
            pass

        return None

    def clear(self) -> None:
        """Clear all cache for this project."""
        import shutil

        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            logger.info(f"Cache cleared for {self.project_name}")

    def get_all_cached_pages(self) -> list[Page]:
        """Get all pages from cache."""
        pages = []
        for filepath in self.pages_dir.glob("*.json"):
            try:
                with open(filepath, encoding="utf-8") as f:
                    data = json.load(f)
                pages.append(
                    Page(
                        url=data["url"],
                        title=data.get("title", ""),
                        html=data.get("html", ""),
                        cleaned_html=data.get("cleaned_html", ""),
                        depth=data.get("depth", 0),
                        order=data.get("order", 0),
                        parent_url=data.get("parent_url"),
                        local_filename=data.get("local_filename", ""),
                        images=data.get("images", []),
                        success=data.get("success", True),
                        error=data.get("error", ""),
                    )
                )
            except (json.JSONDecodeError, IOError, KeyError):
                continue

        pages.sort(key=lambda p: p.order)
        return pages
