"""Progress tracking and display for the conversion process."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
)
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

console = Console()


class ProgressTracker:
    """Tracks and displays progress for various operations."""

    def __init__(self) -> None:
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=40),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=console,
        )

    @contextmanager
    def track(
        self, description: str, total: int
    ) -> Generator[Progress, None, None]:
        """Context manager for tracking progress."""
        with self.progress:
            task = self.progress.add_task(description, total=total)
            yield self.progress
            self.progress.update(task, completed=total)


def show_start_banner() -> None:
    """Display the application start banner."""
    banner = Panel(
        Text.from_markup(
            "[bold cyan]Documentation to EPUB Converter[/]\n"
            "[dim]Transform online documentation into Kindle-compatible EPUB files[/]"
        ),
        border_style="cyan",
    )
    console.print(banner)
    console.print()


def show_url_prompt() -> str:
    """Prompt the user for a URL."""
    console.print("[bold green]Enter the documentation URL:[/]")
    url = console.input("[cyan]> [/]")
    return url.strip()


def show_structure_preview(pages: list[dict]) -> None:
    """Display a preview of the discovered structure."""
    console.print("\n[bold yellow]Discovered Structure:[/]")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Order", style="dim", width=6)
    table.add_column("Title", style="cyan")
    table.add_column("URL", style="blue")
    table.add_column("Depth", style="green", width=6)

    for page in pages[:20]:
        table.add_row(
            str(page.get("order", 0)),
            page.get("title", "Untitled")[:50],
            page.get("url", "")[:60],
            str(page.get("depth", 0)),
        )

    if len(pages) > 20:
        table.add_row("...", f"... and {len(pages) - 20} more pages", "", "")

    console.print(table)


def show_title_prompt(default_title: str) -> str:
    """Prompt the user for a book title."""
    console.print(
        f"\n[bold green]Book title (press Enter for '[cyan]{default_title}[/]'):[/]"
    )
    title = console.input("[cyan]> [/]").strip()
    return title or default_title


def show_progress_bar(description: str, total: int) -> Progress:
    """Create and return a progress bar."""
    progress = Progress(
        SpinnerColumn(),
        TextColumn(f"[bold blue]{description}"),
        BarColumn(bar_width=40),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        console=console,
    )
    return progress


def show_error(message: str) -> None:
    """Display an error message."""
    console.print(f"[bold red]Error:[/] {message}")


def show_warning(message: str) -> None:
    """Display a warning message."""
    console.print(f"[bold yellow]Warning:[/] {message}")


def show_info(message: str) -> None:
    """Display an informational message."""
    console.print(f"[bold blue]Info:[/] {message}")


def show_success(message: str) -> None:
    """Display a success message."""
    console.print(f"[bold green]Success:[/] {message}")


def show_summary(stats: dict) -> None:
    """Display the final conversion summary."""
    console.print()
    summary = Panel(
        Text.from_markup(
            f"[bold cyan]Process Complete![/]\n\n"
            f"Pages found: [green]{stats.get('pages_found', 0)}[/]\n"
            f"Pages processed: [green]{stats.get('pages_processed', 0)}[/]\n"
            f"Pages skipped: [yellow]{stats.get('pages_skipped', 0)}[/]\n"
            f"Images processed: [green]{stats.get('images_processed', 0)}[/]\n"
            f"Images skipped: [yellow]{stats.get('images_skipped', 0)}[/]\n"
            f"EPUB size: [cyan]{stats.get('epub_size', '0 KB')}[/]\n"
            f"Output file: [green]{stats.get('output_file', '')}[/]"
        ),
        title="[bold green]Summary[/]",
        border_style="green",
    )
    console.print(summary)
