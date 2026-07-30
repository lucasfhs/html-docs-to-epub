"""Tests for URL utilities."""
import pytest
from src.utils import (
    normalize_url,
    is_internal_url,
    is_docs_url,
    get_docs_prefix,
    sanitize_filename,
    extract_title_from_url,
    resolve_image_url,
    get_file_extension,
    is_valid_image_url,
    truncate_text,
    get_domain,
)


class TestNormalizeUrl:
    """Tests for URL normalization."""

    def test_remove_utm_source(self):
        url = "https://example.com/docs?utm_source=test&page=1"
        result = normalize_url(url)
        assert "utm_source" not in result
        assert "page=1" in result

    def test_remove_fragment(self):
        url = "https://example.com/docs#section"
        result = normalize_url(url)
        assert "#" not in result

    def test_remove_multiple_tracking_params(self):
        url = "https://example.com?utm_medium=a&utm_campaign=b&ref=c"
        result = normalize_url(url)
        assert "utm_medium" not in result
        assert "utm_campaign" not in result
        assert "ref" not in result

    def test_preserve_path(self):
        url = "https://example.com/docs/install"
        result = normalize_url(url)
        assert result == "https://example.com/docs/install"

    def test_resolve_relative_url(self):
        url = "../other"
        base = "https://example.com/docs/current/"
        result = normalize_url(url, base)
        assert result == "https://example.com/docs/other"

    def test_skip_non_http(self):
        url = "ftp://example.com/file"
        result = normalize_url(url)
        assert result == ""

    def test_empty_url(self):
        result = normalize_url("")
        assert result == ""


class TestIsInternalUrl:
    """Tests for internal URL detection."""

    def test_same_domain(self):
        url = "https://example.com/docs"
        base = "https://example.com/"
        assert is_internal_url(url, base) is True

    def test_different_domain(self):
        url = "https://other.com/docs"
        base = "https://example.com/"
        assert is_internal_url(url, base) is False

    def test_subdomain(self):
        url = "https://sub.example.com/docs"
        base = "https://example.com/"
        assert is_internal_url(url, base) is False

    def test_empty_url(self):
        assert is_internal_url("", "https://example.com") is False

    def test_empty_base(self):
        assert is_internal_url("https://example.com", "") is False


class TestIsDocsUrl:
    """Tests for documentation URL detection."""

    def test_within_docs(self):
        url = "https://example.com/docs/hermes/install"
        prefix = "/docs/hermes"
        assert is_docs_url(url, prefix) is True

    def test_outside_docs(self):
        url = "https://example.com/blog/post"
        prefix = "/docs/hermes"
        assert is_docs_url(url, prefix) is False

    def test_empty_prefix(self):
        url = "https://example.com/anything"
        assert is_docs_url(url, "") is True


class TestSanitizeFilename:
    """Tests for filename sanitization."""

    def test_remove_special_chars(self):
        result = sanitize_filename("file<>:name")
        assert result == "file_name"

    def test_replace_spaces(self):
        result = sanitize_filename("my file name")
        assert result == "my-file-name"

    def test_limit_length(self):
        long_name = "a" * 200
        result = sanitize_filename(long_name)
        assert len(result) <= 100

    def test_lowercase(self):
        result = sanitize_filename("FileName")
        assert result == "filename"

    def test_empty_name(self):
        result = sanitize_filename("")
        assert result == "unnamed"


class TestExtractTitleFromUrl:
    """Tests for title extraction from URL."""

    def test_simple_path(self):
        url = "https://example.com/docs/installation"
        result = extract_title_from_url(url)
        assert result == "Installation"

    def test_multi_level_path(self):
        url = "https://example.com/docs/getting-started/intro"
        result = extract_title_from_url(url)
        assert result == "Intro"

    def test_index_page(self):
        url = "https://example.com/"
        result = extract_title_from_url(url)
        assert result == "Index"


class TestResolveImageUrl:
    """Tests for image URL resolution."""

    def test_relative_url(self):
        src = "../images/logo.png"
        page = "https://example.com/docs/page/"
        result = resolve_image_url(src, page)
        assert result == "https://example.com/docs/images/logo.png"

    def test_absolute_url(self):
        src = "https://example.com/image.png"
        result = resolve_image_url(src, "https://example.com/page")
        assert result == "https://example.com/image.png"

    def test_data_uri(self):
        src = "data:image/png;base64,abc123"
        result = resolve_image_url(src, "https://example.com/page")
        assert result == src

    def test_empty_src(self):
        result = resolve_image_url("", "https://example.com/page")
        assert result == ""


class TestGetFileExtension:
    """Tests for file extension extraction."""

    def test_jpg(self):
        assert get_file_extension("https://example.com/image.jpg") == "jpg"

    def test_png(self):
        assert get_file_extension("https://example.com/image.png") == "png"

    def test_webp(self):
        assert get_file_extension("https://example.com/image.webp") == "webp"

    def test_no_extension(self):
        assert get_file_extension("https://example.com/image") == ""

    def test_query_param(self):
        assert get_file_extension("https://example.com/image.jpg?v=1") == "jpg"


class TestIsValidImageUrl:
    """Tests for valid image URL detection."""

    def test_valid_jpg(self):
        assert is_valid_image_url("https://example.com/image.jpg") is True

    def test_valid_png(self):
        assert is_valid_image_url("https://example.com/image.png") is True

    def test_invalid_pdf(self):
        assert is_valid_image_url("https://example.com/file.pdf") is False

    def test_data_uri(self):
        assert is_valid_image_url("data:image/png;base64,abc") is True

    def test_empty(self):
        assert is_valid_image_url("") is False


class TestTruncateText:
    """Tests for text truncation."""

    def test_short_text(self):
        assert truncate_text("hello", 10) == "hello"

    def test_long_text(self):
        result = truncate_text("hello world", 5)
        assert result == "he..."

    def test_exact_length(self):
        assert truncate_text("hello", 5) == "hello"


class TestGetDomain:
    """Tests for domain extraction."""

    def test_simple_domain(self):
        assert get_domain("https://example.com/path") == "example.com"

    def test_with_www(self):
        assert get_domain("https://www.example.com/path") == "www.example.com"

    def test_with_port(self):
        assert get_domain("https://example.com:8080/path") == "example.com:8080"
