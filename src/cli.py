"""Command-line interface for the documentation to EPUB converter."""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime

from .config import Config
from .progress import (
    show_start_banner,
    show_url_prompt,
    show_title_prompt,
    show_error,
    show_info,
    show_success,
    show_summary,
    console,
)
from .crawler import Crawler
from .cache import Cache
from .chapter_builder import ChapterBuilder
from .epub_builder import EPUBBuilder
from .image_processor import ImageProcessor
from .validator import EPUBValidator
from .models import BookMetadata

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the application."""
    log_level = logging.DEBUG if verbose else logging.INFO
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "conversion.log", encoding="utf-8"),
            logging.StreamHandler(sys.stdout) if verbose else logging.NullHandler(),
        ],
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Convert online documentation to Kindle-compatible EPUB",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("url", nargs="?", help="Documentation URL")
    parser.add_argument("--output", "-o", help="Output EPUB file path")
    parser.add_argument("--title", "-t", help="Book title")
    parser.add_argument("--author", "-a", help="Book author")
    parser.add_argument(
        "--max-pages", type=int, default=500, help="Maximum pages to process (default: 500)"
    )
    parser.add_argument(
        "--workers", type=int, default=5, help="Number of concurrent workers (default: 5)"
    )
    parser.add_argument(
        "--delay", type=float, default=0.3, help="Delay between requests in seconds (default: 0.3)"
    )
    parser.add_argument(
        "--image-quality", type=int, default=80, help="JPEG image quality (default: 80)"
    )
    parser.add_argument(
        "--max-image-width", type=int, default=1200, help="Maximum image width in pixels (default: 1200)"
    )
    parser.add_argument(
        "--use-playwright", action="store_true", help="Use Playwright for JavaScript-rendered pages"
    )
    parser.add_argument(
        "--force", action="store_true", help="Ignore cache and start fresh"
    )
    parser.add_argument(
        "--no-images", action="store_true", help="Exclude images from the EPUB"
    )
    parser.add_argument("--include", help="Regex pattern for URLs to include")
    parser.add_argument("--exclude", help="Regex pattern for URLs to exclude")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")

    # Send to Kindle options
    parser.add_argument(
        "--send-to-kindle",
        action="store_true",
        help="Send the EPUB to Kindle via email after generation",
    )
    parser.add_argument("--kindle-email", help="Kindle email address (e.g. user@kindle.com)")
    parser.add_argument("--smtp-email", help="Sender email address for SMTP")
    parser.add_argument("--smtp-password", help="Sender email password or app password")
    parser.add_argument("--smtp-server", help="SMTP server address (auto-detected from email)")
    parser.add_argument(
        "--smtp-port", type=int, default=587, help="SMTP server port (default: 587)"
    )
    parser.add_argument(
        "--smtp-no-tls",
        action="store_true",
        help="Disable TLS encryption for SMTP connection",
    )

    return parser.parse_args()


def get_config_interactive() -> Config:
    """Get configuration interactively from the user."""
    show_start_banner()

    config = Config()

    # Get URL
    config.url = show_url_prompt()
    if not config.url:
        show_error("URL is required")
        sys.exit(1)

    # Ensure URL has scheme
    if not config.url.startswith(("http://", "https://")):
        config.url = "https://" + config.url

    # Ask about sending to Kindle
    console.print()
    console.print("[bold green]Send to Kindle?[/]")
    send_choice = console.input("[cyan]Send EPUB to Kindle via email? (y/n) > [/]").strip().lower()
    if send_choice in ("y", "yes", "s", "sim"):
        config.send_to_kindle = True

        # Load credentials from .env if available
        _load_env_credentials(config)

        # Kindle email
        if not config.kindle_email:
            console.print("[bold green]Kindle email address:[/]")
            console.print("[dim]  (found in Kindle Settings > Your Account)[/]")
            config.kindle_email = console.input("[cyan]> [/]").strip()

        # Sender email (SMTP)
        if not config.smtp_email:
            console.print("[bold green]Your email address (sender):[/]")
            console.print("[dim]  (Gmail, Outlook, Yahoo, etc.)[/]")
            config.smtp_email = console.input("[cyan]> [/]").strip()

        # Sender password / app password
        if not config.smtp_password:
            console.print("[bold green]Email password or app password:[/]")
            console.print("[dim]  (For Gmail, use an App Password)[/]")
            config.smtp_password = console.input("[cyan]> [/]").strip()

    return config


def get_config_from_args(args: argparse.Namespace) -> Config:
    """Get configuration from command-line arguments."""
    config = Config()

    config.url = args.url
    if not config.url.startswith(("http://", "https://")):
        config.url = "https://" + config.url

    if args.output:
        config.output = args.output
    if args.title:
        config.title = args.title
    if args.author:
        config.author = args.author

    config.max_pages = args.max_pages
    config.workers = args.workers
    config.delay = args.delay
    config.image_quality = args.image_quality
    config.max_image_width = args.max_image_width
    config.use_playwright = args.use_playwright
    config.force = args.force
    config.no_images = args.no_images
    config.include_pattern = args.include or ""
    config.exclude_pattern = args.exclude or ""
    config.verbose = args.verbose

    # Send to Kindle settings
    config.send_to_kindle = args.send_to_kindle
    config.kindle_email = args.kindle_email or ""
    config.smtp_email = args.smtp_email or ""
    config.smtp_password = args.smtp_password or ""
    config.smtp_server = args.smtp_server or ""
    config.smtp_port = args.smtp_port
    config.smtp_use_tls = not args.smtp_no_tls

    return config


def generate_default_title(url: str) -> str:
    """Generate a default title from the URL."""
    from urllib.parse import urlparse
    from .utils import extract_title_from_url

    parsed = urlparse(url)
    domain = parsed.netloc.replace("www.", "")

    # Try to get a meaningful path part
    parts = [p for p in parsed.path.split("/") if p]
    if parts:
        return f"{parts[-1].replace('-', ' ').title()} Documentation"

    return f"{domain} Documentation"


def _load_env_credentials(config: Config) -> None:
    """Load SMTP credentials from .env file if available."""
    try:
        from dotenv import load_dotenv
        import os

        load_dotenv()

        if not config.kindle_email:
            config.kindle_email = os.getenv("KINDLE_EMAIL", "")
        if not config.smtp_email:
            config.smtp_email = os.getenv("SMTP_EMAIL", "")
        if not config.smtp_password:
            config.smtp_password = os.getenv("SMTP_PASSWORD", "")
        if not config.smtp_server:
            config.smtp_server = os.getenv("SMTP_SERVER", "")
        if config.smtp_port == 587:
            port_str = os.getenv("SMTP_PORT", "")
            if port_str:
                config.smtp_port = int(port_str)
        tls_str = os.getenv("SMTP_USE_TLS", "")
        if tls_str:
            config.smtp_use_tls = tls_str.lower() in ("true", "1", "yes", "on")

        if config.kindle_email or config.smtp_email:
            show_info("Loaded email credentials from .env file")
    except ImportError:
        pass


def run_conversion(config: Config) -> None:
    """Run the main conversion process."""
    import time
    import shutil

    from .progress import ProgressTracker
    from .utils import sanitize_filename

    setup_logging(config.verbose)
    show_info(f"Starting conversion for: {config.url}")

    # Initialize cache
    cache = Cache(config)

    # Check for incomplete process
    if cache.has_incomplete_process() and not config.force:
        console.print(
            "[bold yellow]An incomplete processing session was found.[/]"
        )
        console.print("1. Continue processing")
        console.print("2. Restart processing")
        console.print("3. Cancel")
        choice = console.input("[cyan]> [/]").strip()

        if choice == "1":
            show_info("Continuing previous session...")
        elif choice == "2":
            cache.clear()
            cache = Cache(config)
            show_info("Starting fresh...")
        else:
            show_info("Cancelled.")
            return

    # Start session
    cache.start_session()
    start_time = time.time()

    try:
        # Phase 1: Crawl
        show_info("Phase 1: Discovering pages...")
        crawler = Crawler(config, cache)
        result = crawler.crawl()

        if not result.pages:
            show_error("No pages found. Check the URL and try again.")
            return

        # Generate title if not provided
        if not config.title:
            config.title = generate_default_title(config.url)

        # Generate output filename
        if not config.output:
            output_filename = sanitize_filename(config.title) + ".epub"
            config.output_dir.mkdir(parents=True, exist_ok=True)
            config.output = str(config.output_dir / output_filename)

        # Ensure output directory exists
        output_path = Path(config.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Create temporary directories
        temp_dir = Path(".cache") / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        images_dir = temp_dir / "images"
        images_dir.mkdir(exist_ok=True)

        # Phase 2: Process images and build chapters
        show_info("Phase 2: Processing content...")
        image_processor = None
        if not config.no_images:
            image_processor = ImageProcessor(config)

        chapter_builder = ChapterBuilder(config)
        chapters = chapter_builder.build_chapters(
            result.pages, images_dir, image_processor
        )

        # Phase 3: Build EPUB
        show_info("Phase 3: Building EPUB...")
        metadata = BookMetadata(
            title=config.title,
            author=config.author or "Documentation Converter",
            source_url=config.url,
            generation_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

        epub_builder = EPUBBuilder(config)
        css_path = Path("assets/book.css")
        epub_builder.build(chapters, metadata, images_dir, css_path)
        epub_builder.save(output_path)

        # Phase 4: Validate
        show_info("Phase 4: Validating EPUB...")
        validator = EPUBValidator()
        is_valid, errors, warnings = validator.validate(output_path)

        if not is_valid:
            show_error("EPUB validation failed:")
            for error in errors:
                console.print(f"  [red]✗[/] {error}")
        else:
            show_success("EPUB is valid!")

        if warnings:
            for warning in warnings:
                console.print(f"  [yellow]⚠[/] {warning}")

        # Calculate statistics
        elapsed_time = time.time() - start_time
        epub_size = output_path.stat().st_size / (1024 * 1024)

        images_processed = 0
        images_skipped = 0
        if image_processor:
            images_processed, images_skipped = image_processor.get_stats()

        stats = {
            "pages_found": len(result.pages),
            "pages_processed": len(chapters),
            "pages_skipped": len(result.failed_urls),
            "images_processed": images_processed,
            "images_skipped": images_skipped,
            "epub_size": f"{epub_size:.1f} MB",
            "output_file": str(output_path),
        }

        # Phase 5: Send to Kindle (if enabled)
        if config.send_to_kindle and config.kindle_email and config.smtp_email and config.smtp_password:
            show_info("Phase 5: Sending to Kindle...")
            from .sender import send_to_kindle

            sent = send_to_kindle(
                epub_path=output_path,
                kindle_email=config.kindle_email,
                sender_email=config.smtp_email,
                sender_password=config.smtp_password,
                smtp_server=config.smtp_server,
                smtp_port=config.smtp_port,
                use_tls=config.smtp_use_tls,
            )
            stats["sent_to_kindle"] = sent
        elif config.send_to_kindle:
            # Missing credentials in CLI mode - warn the user
            show_warning(
                "Send to Kindle was requested but credentials are missing.\n"
                "  Provide --kindle-email, --smtp-email, and --smtp-password."
            )

        # Complete session
        cache.complete_session(stats)

        # Show summary
        show_summary(stats)

        # Cleanup temp directory
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)

    except KeyboardInterrupt:
        show_info("Process interrupted by user.")
        show_info("You can resume later by running the command again.")
    except Exception as e:
        logger.exception(f"Conversion failed: {e}")
        show_error(f"Conversion failed: {e}")
    finally:
        if image_processor:
            image_processor.close()


def main() -> None:
    """Main entry point for the CLI."""
    args = parse_args()

    if args.url:
        # Non-interactive mode
        config = get_config_from_args(args)
    else:
        # Interactive mode
        config = get_config_interactive()

    run_conversion(config)


if __name__ == "__main__":
    main()
