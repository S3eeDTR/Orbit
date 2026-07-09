# ORBIT UI Module
# Provides rendering functions for terminal-based UI using Rich library

from __future__ import annotations

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text

console = Console()


# ============================================================================
# MARKDOWN
# ============================================================================

def render_markdown(text: str) -> None:
    """Render Markdown with a plain-text fallback."""
    try:
        console.print(Markdown(text))
    except Exception:
        console.print(text)


# ============================================================================
# STREAMING
# ============================================================================

def stream_text(chunk: str) -> None:
    """Write one streamed chunk without adding a newline."""
    console.print(chunk, end="", soft_wrap=True)


def finish_stream() -> None:
    """Finish a streamed response."""
    console.print()


# ============================================================================
# CODE
# ============================================================================

def render_code(
    code: str,
    language: str = "python",
) -> None:
    """Render syntax highlighted code."""
    console.print(
        Syntax(
            code,
            language,
            theme="monokai",
            line_numbers=True,
            word_wrap=True,
        )
    )


# ============================================================================
# STATUS MESSAGES
# ============================================================================

def ok(message: str) -> None:
    console.print(f"[green]{message}[/green]")


def warn(message: str) -> None:
    console.print(f"[yellow]{message}[/yellow]")


def error(message: str) -> None:
    console.print(f"[red]{message}[/red]")


def info(message: str) -> None:
    console.print(f"[cyan]{message}[/cyan]")


# ============================================================================
# PANELS
# ============================================================================

def panel(
    message: str,
    title: str | None = None,
    border_style: str = "cyan",
) -> None:
    console.print(
        Panel(
            message,
            title=title,
            border_style=border_style,
        )
    )


def info_panel(
    message: str,
    title: str = "Information",
) -> None:
    panel(message, title=title)


def success_panel(
    message: str,
    title: str = "Success",
) -> None:
    panel(message, title=title, border_style="green")


def warning_panel(
    message: str,
    title: str = "Warning",
) -> None:
    panel(message, title=title, border_style="yellow")


def error_panel(
    message: str,
    title: str = "Error",
) -> None:
    panel(message, title=title, border_style="red")


# ============================================================================
# HEADINGS
# ============================================================================

def heading(text: str) -> None:
    console.rule(
        Text(
            text,
            style="bold orange1",
        )
    )
