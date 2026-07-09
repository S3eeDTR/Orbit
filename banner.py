from __future__ import annotations

from pathlib import Path

from rich.align import Align
from rich.columns import Columns
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .constants import APP_NAME, APP_VERSION, PROJECT_INSTRUCTIONS_FILE
from .project import ProjectInfo
from .sessions import RecentActivity
from .ui import console

ROBOT = r"""
     ██████
   ██      ██
   ██  ██  ██
   ██      ██
     ██████
    ██ ██ ██
"""


def render_startup(model: str, project: ProjectInfo, recent: RecentActivity) -> None:
    title = Text(f"{APP_NAME} v{APP_VERSION}", style="bold orange1")
    console.rule(title, style="orange1")

    left = Table.grid(padding=(0, 1))
    left.add_row(Text("Welcome back!", style="bold white"))
    left.add_row(Text(ROBOT, style="orange1"))
    left.add_row(Text(f"Model: {model}", style="dim"))
    left.add_row(Text(f"Project: {project.root}", style="dim"))
    left.add_row(Text(f"Files indexed: {project.file_count}", style="dim"))

    tips = Table.grid(padding=(0, 1))
    tips.add_row(Text("Tips for getting started", style="bold orange1"))
    tips.add_row(Text(f"/init      create {PROJECT_INSTRUCTIONS_FILE} project instructions", style="white"))
    tips.add_row(Text("/index     scan project files", style="white"))
    tips.add_row(Text("@file.py   attach file content to a prompt", style="white"))
    tips.add_row(Text("/model     choose model, /files show indexed files", style="white"))
    tips.add_row("")
    tips.add_row(Text("Recent activity", style="bold orange1"))
    if recent.items:
        for item in recent.items[:5]:
            tips.add_row(Text(f"• {item}", style="dim"))
    else:
        tips.add_row(Text("No recent activity", style="dim"))

    console.print(Panel(Columns([left, tips], equal=False, expand=True), border_style="orange1"))
    console.print(Panel("Type a message, use [bold]@file.py[/bold], or run [bold]/help[/bold].", border_style="bright_black"))


def render_prompt_hint() -> None:
    console.print(Align.left(Text("Thinking on Enter • multiline with Esc+Enter • Ctrl+C to cancel", style="dim blue")))
