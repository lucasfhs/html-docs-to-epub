"""Tests for HTML cleaner."""
import pytest
from src.cleaner import HTMLCleaner
from src.config import Config


@pytest.fixture
def cleaner():
    config = Config()
    return HTMLCleaner(config)


class TestHTMLCleaner:
    """Tests for HTML cleaning functionality."""

    def test_remove_scripts(self, cleaner):
        html = "<div><p>Content</p><script>alert('test')</script></div>"
        result = cleaner.clean(html)
        assert "script" not in result
        assert "Content" in result

    def test_remove_styles(self, cleaner):
        html = "<div><p>Text</p><style>.class { color: red; }</style></div>"
        result = cleaner.clean(html)
        assert "<style>" not in result

    def test_remove_nav_elements(self, cleaner):
        html = """
        <div>
            <nav><a href="/home">Home</a></nav>
            <p>Main content</p>
        </div>
        """
        result = cleaner.clean(html)
        assert "Main content" in result

    def test_preserve_code_blocks(self, cleaner):
        html = "<pre><code>print('hello')</code></pre>"
        result = cleaner.clean(html)
        assert "print('hello')" in result

    def test_preserve_tables(self, cleaner):
        html = """
        <table>
            <tr><th>Name</th><th>Value</th></tr>
            <tr><td>A</td><td>1</td></tr>
        </table>
        """
        result = cleaner.clean(html)
        assert "<table>" in result
        assert "Name" in result

    def test_remove_empty_elements(self, cleaner):
        html = "<div><p>Content</p><p></p><span></span></div>"
        result = cleaner.clean(html)
        assert "Content" in result

    def test_clean_attributes(self, cleaner):
        html = '<a href="/link" onclick="handler()" data-test="val">Link</a>'
        result = cleaner.clean(html)
        assert "onclick" not in result
        assert "data-test" not in result
        assert 'href="/link"' in result

    def test_preserve_headings(self, cleaner):
        html = "<h1 id='test'>Title</h1><h2>Subtitle</h2>"
        result = cleaner.clean(html)
        assert "<h1" in result
        assert "<h2" in result

    def test_empty_html(self, cleaner):
        result = cleaner.clean("")
        assert result == ""

    def test_preserve_images(self, cleaner):
        html = '<img src="image.png" alt="Description">'
        result = cleaner.clean(html)
        assert "<img" in result
        assert 'alt="Description"' in result

    def test_remove_hidden_elements(self, cleaner):
        html = """
        <div style="display: none">Hidden</div>
        <div>Visible</div>
        """
        result = cleaner.clean(html)
        assert "Hidden" not in result
        assert "Visible" in result

    def test_clean_blockquotes(self, cleaner):
        html = "<blockquote><p>Quote</p></blockquote>"
        result = cleaner.clean(html)
        assert "<blockquote>" in result
        assert "Quote" in result
