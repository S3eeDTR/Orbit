from __future__ import annotations

from rich.align import Align
from rich.columns import Columns
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .constants import APP_DISPLAY_NAME, APP_VERSION, PROJECT_INSTRUCTIONS_FILE
from .project import ProjectInfo
from .sessions import RecentActivity
from .ui import console


ORBIT_MARK = r"""
      ██████
    ██      ██
    ██  ██  ██
    ██      ██
      ██████
     ██ ██ ██
"""


def render_startup(
    model: str,
    project: ProjectInfo,
    recent: RecentActivity,
) -> None:
    """Render the startup dashboard."""

    title = Text(
        f"{APP_DISPLAY_NAME} v{APP_VERSION}",
        style="bold orange1",
    )

    console.rule(title, style="orange1")

    left = Table.grid(padding=(0, 1))
    left.add_row(Text("Welcome back", style="bold white"))
    left.add_row(Text(ORBIT_MARK, style="orange1"))
    left.add_row(Text(f"Model: {model}", style="dim"))
    left.add_row(Text(f"Project: {project.root}", style="dim"))
    left.add_row(Text(f"Files indexed: {project.file_count}", style="dim"))

    right = Table.grid(padding=(0, 1))
    right.add_row(Text("Getting started", style="bold orange1"))
    right.add_row(
        Text(
            f"/init      create {PROJECT_INSTRUCTIONS_FILE}",
            style="white",
        )
    )
    right.add_row(Text("/index     scan project files", style="white"))
    right.add_row(Text("/files     show indexed files", style="white"))
    right.add_row(Text("/model     choose or switch model", style="white"))
    right.add_row(Text("@file.py   attach file content", style="white"))
    right.add_row("")

    right.add_row(Text("Recent activity", style="bold orange1"))

    if recent.items:
        for item in recent.items[:5]:
            right.add_row(Text(f"- {item}", style="dim"))
    else:
        right.add_row(Text("No recent activity", style="dim"))

    dashboard = Columns(
        [left, right],
        equal=False,
        expand=True,
    )

    console.print(
        Panel(
            dashboard,
            border_style="orange1",
            padding=(1, 2),
        )
    )


def render_prompt_hint() -> None:
    """Render prompt usage hint."""

    console.print(
        Align.left(
            Text(
                "Enter • Esc+Enter for multiline • Ctrl+C",
                style="dim blue",
            )
        )
    )
