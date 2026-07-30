"""Tests for content extractor."""
import pytest
from src.extractor import ContentExtractor
from src.config import Config


@pytest.fixture
def extractor():
    config = Config()
    return ContentExtractor(config)


class TestContentExtractor:
    """Tests for content extraction functionality."""

    def test_extract_main_content(self, extractor):
        html = """
        <html>
        <body>
            <nav>Navigation</nav>
            <main>
                <h1>Title</h1>
                <p>Main content here.</p>
            </main>
            <footer>Footer</footer>
        </body>
        </html>
        """
        result = extractor.extract(html)
        assert "Main content here" in result
        assert "Navigation" not in result

    def test_extract_with_article(self, extractor):
        html = """
        <html>
        <body>
            <header>Header</header>
            <article>
                <h1>Article Title</h1>
                <p>Article content.</p>
            </article>
        </body>
        </html>
        """
        result = extractor.extract(html)
        assert "Article content" in result

    def test_extract_with_content_class(self, extractor):
        html = """
        <html>
        <body>
            <div class="sidebar">Sidebar</div>
            <div class="content">
                <p>Page content.</p>
            </div>
        </body>
        </html>
        """
        result = extractor.extract(html)
        assert "Page content" in result

    def test_heuristic_extraction(self, extractor):
        html = """
        <html>
        <body>
            <div class="unknown">
                <p>This is a paragraph with enough text to be considered content.</p>
                <p>Another paragraph with more text content.</p>
            </div>
        </body>
        </html>
        """
        result = extractor.extract(html)
        assert "paragraph" in result.lower()

    def test_empty_html(self, extractor):
        result = extractor.extract("")
        assert result == ""

    def test_extract_title_h1(self, extractor):
        html = "<html><body><h1>My Title</h1><p>Content</p></body></html>"
        result = extractor.extract(html)
        assert "My Title" in result

    def test_extract_table_of_contents(self, extractor):
        html = """
        <html>
        <body>
            <h1>Chapter 1</h1>
            <h2>Section 1.1</h2>
            <h2>Section 1.2</h2>
            <h3>Subsection 1.2.1</h3>
        </body>
        </html>
        """
        toc = extractor.extract_table_of_contents(html)
        assert len(toc) == 4
        assert toc[0]["level"] == 1
        assert toc[1]["level"] == 2

    def test_preserve_code_blocks(self, extractor):
        html = """
        <div class="content">
            <pre><code>def hello():
    print("world")</code></pre>
        </div>
        """
        result = extractor.extract(html)
        assert "def hello" in result

    def test_preserve_lists(self, extractor):
        html = """
        <div class="content">
            <ul>
                <li>Item 1</li>
                <li>Item 2</li>
            </ul>
        </div>
        """
        result = extractor.extract(html)
        assert "Item 1" in result
        assert "Item 2" in result

    def test_no_content_found(self, extractor):
        html = "<html><body><nav>Only navigation</nav></body></html>"
        result = extractor.extract(html)
        # Should fallback to body or return something
        assert result is not None
