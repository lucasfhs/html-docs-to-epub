"""Tests for link converter."""
import pytest
from src.link_converter import LinkConverter
from src.models import Page


@pytest.fixture
def sample_pages():
    return [
        Page(
            url="https://example.com/docs/intro",
            title="Introduction",
            local_filename="001-intro.xhtml",
        ),
        Page(
            url="https://example.com/docs/install",
            title="Installation",
            local_filename="002-install.xhtml",
        ),
        Page(
            url="https://example.com/docs/config",
            title="Configuration",
            local_filename="003-config.xhtml",
        ),
    ]


@pytest.fixture
def converter(sample_pages):
    return LinkConverter(sample_pages)


class TestLinkConverter:
    """Tests for link conversion functionality."""

    def test_convert_internal_link(self, converter):
        html = '<a href="https://example.com/docs/install">Install</a>'
        current_page = Page(
            url="https://example.com/docs/intro",
            title="Intro",
            local_filename="001-intro.xhtml",
        )
        result = converter.convert_links(html, current_page)
        assert 'href="002-install.xhtml"' in result

    def test_keep_external_link(self, converter):
        html = '<a href="https://google.com">Google</a>'
        current_page = Page(
            url="https://example.com/docs/intro",
            title="Intro",
            local_filename="001-intro.xhtml",
        )
        result = converter.convert_links(html, current_page)
        assert 'href="https://google.com"' in result

    def test_convert_relative_link(self, converter):
        html = '<a href="install">Install</a>'
        current_page = Page(
            url="https://example.com/docs/intro",
            title="Intro",
            local_filename="001-intro.xhtml",
        )
        result = converter.convert_links(html, current_page)
        # Should resolve to internal link
        assert 'href="002-install.xhtml"' in result

    def test_skip_anchors(self, converter):
        html = '<a href="#section">Section</a>'
        current_page = Page(
            url="https://example.com/docs/intro",
            title="Intro",
            local_filename="001-intro.xhtml",
        )
        result = converter.convert_links(html, current_page)
        assert 'href="#section"' in result

    def test_skip_mailto(self, converter):
        html = '<a href="mailto:test@example.com">Email</a>'
        current_page = Page(
            url="https://example.com/docs/intro",
            title="Intro",
            local_filename="001-intro.xhtml",
        )
        result = converter.convert_links(html, current_page)
        assert 'href="mailto:test@example.com"' in result

    def test_get_internal_links(self, converter):
        html = """
        <a href="https://example.com/docs/install">Install</a>
        <a href="https://google.com">External</a>
        <a href="https://example.com/docs/config">Config</a>
        """
        links = converter.get_internal_links(html, "https://example.com/docs/intro")
        assert len(links) == 2

    def test_convert_anchor_in_same_page(self, converter):
        html = '<a href="https://example.com/docs/config#section">Section</a>'
        current_page = Page(
            url="https://example.com/docs/intro",
            title="Intro",
            local_filename="001-intro.xhtml",
        )
        result = converter.convert_links(html, current_page)
        assert 'href="003-config.xhtml#section"' in result
