"""Tests for crawler."""
import pytest
from src.crawler import Crawler
from src.config import Config
from src.cache import Cache


@pytest.fixture
def config():
    return Config(url="https://example.com/docs")


@pytest.fixture
def cache(config):
    return Cache(config, project_name="test-project")


class TestCrawler:
    """Tests for crawler functionality."""

    def test_should_visit_internal(self, config, cache):
        crawler = Crawler(config, cache)
        assert crawler._should_visit("https://example.com/docs/page") is True

    def test_should_visit_external(self, config, cache):
        crawler = Crawler(config, cache)
        assert crawler._should_visit("https://other.com/page") is False

    def test_should_visit_excluded_pattern(self, config, cache):
        config.exclude_pattern = r"/blog"
        crawler = Crawler(config, cache)
        assert crawler._should_visit("https://example.com/docs/blog") is False

    def test_should_visit_include_pattern(self, config, cache):
        config.include_pattern = r"/docs/api"
        crawler = Crawler(config, cache)
        assert crawler._should_visit("https://example.com/docs/api") is True
        assert crawler._should_visit("https://example.com/docs/other") is False

    def test_should_visit_login_page(self, config, cache):
        crawler = Crawler(config, cache)
        assert crawler._should_visit("https://example.com/docs/login") is False

    def test_should_visit_admin_page(self, config, cache):
        crawler = Crawler(config, cache)
        assert crawler._should_visit("https://example.com/docs/admin") is False

    def test_generate_filename(self, config, cache):
        crawler = Crawler(config, cache)
        filename = crawler._generate_filename(
            "https://example.com/docs/installation", 1
        )
        assert filename.endswith(".xhtml")
        assert "001" in filename
