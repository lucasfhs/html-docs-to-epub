"""Image processing and optimization for EPUB."""
from __future__ import annotations

import hashlib
import io
import logging
from pathlib import Path
from urllib.parse import urlparse

import httpx
from PIL import Image

from .config import Config
from .models import ImageInfo
from .utils import resolve_image_url, get_file_extension

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Processes and optimizes images for EPUB inclusion."""

    def __init__(self, config: Config):
        self.config = config
        self.client = httpx.Client(
            timeout=config.timeout,
            follow_redirects=True,
            headers={"User-Agent": config.user_agent},
        )
        self.processed_count = 0
        self.failed_count = 0

    def process_images(
        self, html: str, page_url: str, output_dir: Path
    ) -> tuple[str, list[ImageInfo]]:
        """Process all images in HTML content."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "lxml")
        images = []

        for img in soup.find_all("img"):
            src = img.get("src", "")
            if not src:
                continue

            # Resolve the image URL
            absolute_url = resolve_image_url(src, page_url)

            # Skip data URIs (they're already inline)
            if absolute_url.startswith("data:"):
                continue

            # Process the image
            image_info = self._process_single_image(
                absolute_url, img.get("alt", ""), output_dir
            )

            if image_info and image_info.success:
                images.append(image_info)
                # Update the src in HTML
                img["src"] = image_info.local_path
                self.processed_count += 1
            else:
                self.failed_count += 1
                # Remove the image if it failed
                img.decompose()

        return str(soup), images

    def _process_single_image(
        self, url: str, alt_text: str, output_dir: Path
    ) -> ImageInfo | None:
        """Download and process a single image."""
        try:
            # Download the image
            response = self.client.get(url)
            response.raise_for_status()

            content_type = response.headers.get("content-type", "")
            image_data = response.content

            # Check if it's actually an image
            if not self._is_valid_image(content_type, image_data):
                logger.debug(f"Not a valid image: {url}")
                return ImageInfo(url=url, success=False)

            # Open with Pillow
            img = Image.open(io.BytesIO(image_data))

            # Convert to RGB if necessary
            if img.mode in ("RGBA", "LA", "P"):
                # Create a white background for transparency
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                img = background
            elif img.mode != "RGB":
                img = img.convert("RGB")

            # Resize if too large
            if img.width > self.config.max_image_width:
                ratio = self.config.max_image_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize(
                    (self.config.max_image_width, new_height), Image.Resampling.LANCZOS
                )

            # Generate unique filename
            filename = self._generate_filename(url)
            filepath = output_dir / filename

            # Save the image
            img.save(
                filepath,
                "JPEG",
                quality=self.config.image_quality,
                optimize=True,
            )

            return ImageInfo(
                url=url,
                local_path=filename,
                alt_text=alt_text,
                width=img.width,
                height=img.height,
                format="JPEG",
                success=True,
            )

        except httpx.HTTPError as e:
            logger.warning(f"Failed to download image {url}: {e}")
            return ImageInfo(url=url, success=False)

        except Exception as e:
            logger.warning(f"Failed to process image {url}: {e}")
            return ImageInfo(url=url, success=False)

    def _is_valid_image(self, content_type: str, data: bytes) -> bool:
        """Check if the data is a valid image."""
        # Check content type
        valid_types = ["image/jpeg", "image/png", "image/gif", "image/webp", "image/svg+xml"]
        if any(t in content_type for t in valid_types):
            return True

        # Check magic bytes
        magic_bytes = {
            b"\xff\xd8\xff": "JPEG",
            b"\x89PNG": "PNG",
            b"GIF8": "GIF",
            b"RIFF": "WEBP",
            b"<svg": "SVG",
        }

        for magic, format_name in magic_bytes.items():
            if data[:len(magic)] == magic:
                return True

        return False

    def _generate_filename(self, url: str) -> str:
        """Generate a unique filename for an image."""
        # Use hash of URL for uniqueness
        url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
        ext = get_file_extension(url)

        # Convert webp to jpg
        if ext == "webp":
            ext = "jpg"

        return f"img-{url_hash}.{ext}"

    def close(self) -> None:
        """Close the HTTP client."""
        self.client.close()

    def get_stats(self) -> tuple[int, int]:
        """Get processing statistics."""
        return self.processed_count, self.failed_count
