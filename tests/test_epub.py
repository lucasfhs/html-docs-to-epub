"""Tests for EPUB generation."""
import pytest
from pathlib import Path
import tempfile

from src.epub_builder import EPUBBuilder
from src.config import Config
from src.models import Chapter, BookMetadata


@pytest.fixture
def config():
    return Config()


@pytest.fixture
def sample_chapters():
    return [
        Chapter(
            title="Introduction",
            filename="001-intro.xhtml",
            content="<p>Welcome to the documentation.</p>",
            level=1,
        ),
        Chapter(
            title="Installation",
            filename="002-install.xhtml",
            content="<p>How to install the software.</p>",
            level=1,
        ),
    ]


@pytest.fixture
def sample_metadata():
    return BookMetadata(
        title="Test Documentation",
        author="Test Author",
        source_url="https://example.com/docs",
        generation_date="2024-01-01 00:00:00",
    )


class TestEPUBBuilder:
    """Tests for EPUB generation functionality."""

    def test_build_epub(self, config, sample_chapters, sample_metadata):
        with tempfile.TemporaryDirectory() as tmpdir:
            images_dir = Path(tmpdir) / "images"
            images_dir.mkdir()
            css_path = Path("assets/book.css")
            output_path = Path(tmpdir) / "test.epub"

            builder = EPUBBuilder(config)
            builder.build(sample_chapters, sample_metadata, images_dir, css_path)
            builder.save(output_path)

            assert output_path.exists()
            assert output_path.stat().st_size > 0

    def test_epub_contains_chapters(self, config, sample_chapters, sample_metadata):
        import zipfile

        with tempfile.TemporaryDirectory() as tmpdir:
            images_dir = Path(tmpdir) / "images"
            images_dir.mkdir()
            css_path = Path("assets/book.css")
            output_path = Path(tmpdir) / "test.epub"

            builder = EPUBBuilder(config)
            builder.build(sample_chapters, sample_metadata, images_dir, css_path)
            builder.save(output_path)

            with zipfile.ZipFile(output_path, "r") as zf:
                file_list = zf.namelist()
                assert any("001-intro.xhtml" in f for f in file_list)
                assert any("002-install.xhtml" in f for f in file_list)

    def test_epub_has_metadata(self, config, sample_chapters, sample_metadata):
        import zipfile

        with tempfile.TemporaryDirectory() as tmpdir:
            images_dir = Path(tmpdir) / "images"
            images_dir.mkdir()
            css_path = Path("assets/book.css")
            output_path = Path(tmpdir) / "test.epub"

            builder = EPUBBuilder(config)
            builder.build(sample_chapters, sample_metadata, images_dir, css_path)
            builder.save(output_path)

            with zipfile.ZipFile(output_path, "r") as zf:
                # Find the OPF file
                opf_file = next((f for f in zf.namelist() if f.endswith("content.opf")), None)
                assert opf_file is not None
                opf_content = zf.read(opf_file).decode("utf-8")
                assert "Test Documentation" in opf_content
                assert "Test Author" in opf_content

    def test_epub_has_toc(self, config, sample_chapters, sample_metadata):
        import zipfile

        with tempfile.TemporaryDirectory() as tmpdir:
            images_dir = Path(tmpdir) / "images"
            images_dir.mkdir()
            css_path = Path("assets/book.css")
            output_path = Path(tmpdir) / "test.epub"

            builder = EPUBBuilder(config)
            builder.build(sample_chapters, sample_metadata, images_dir, css_path)
            builder.save(output_path)

            with zipfile.ZipFile(output_path, "r") as zf:
                file_list = zf.namelist()
                assert any("toc.ncx" in f for f in file_list)
                assert any("nav" in f for f in file_list)

    def test_epub_has_css(self, config, sample_chapters, sample_metadata):
        import zipfile

        with tempfile.TemporaryDirectory() as tmpdir:
            images_dir = Path(tmpdir) / "images"
            images_dir.mkdir()
            css_path = Path("assets/book.css")
            output_path = Path(tmpdir) / "test.epub"

            builder = EPUBBuilder(config)
            builder.build(sample_chapters, sample_metadata, images_dir, css_path)
            builder.save(output_path)

            with zipfile.ZipFile(output_path, "r") as zf:
                file_list = zf.namelist()
                assert any("style/default.css" in f for f in file_list)

    def test_epub_mimetype(self, config, sample_chapters, sample_metadata):
        import zipfile

        with tempfile.TemporaryDirectory() as tmpdir:
            images_dir = Path(tmpdir) / "images"
            images_dir.mkdir()
            css_path = Path("assets/book.css")
            output_path = Path(tmpdir) / "test.epub"

            builder = EPUBBuilder(config)
            builder.build(sample_chapters, sample_metadata, images_dir, css_path)
            builder.save(output_path)

            with zipfile.ZipFile(output_path, "r") as zf:
                mimetype = zf.read("mimetype").decode("utf-8").strip()
                assert mimetype == "application/epub+zip"
