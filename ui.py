from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()


def render_markdown(text: str) -> None:
    try:
        console.print(Markdown(text))
    except Exception:
        console.print(text)


def render_code(code: str, language: str = "python") -> None:
    console.print(Syntax(code, language, theme="monokai", line_numbers=True))


def error(message: str) -> None:
    console.print(f"[red]❌ {message}[/red]")


def warn(message: str) -> None:
    console.print(f"[yellow]⚠️ {message}[/yellow]")


def ok(message: str) -> None:
    console.print(f"[green]✅ {message}[/green]")


def info_panel(text: str, title: str = "Info") -> None:
    console.print(Panel(text, title=title, border_style="cyan"))
