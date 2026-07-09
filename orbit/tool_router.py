from __future__ import annotations

import re
from dataclasses import dataclass

from rich.panel import Panel

from .terminal import Terminal
from .ui import console, warn


@dataclass
class ToolResult:
    handled: bool


class ToolRouter:
    """
    Routes simple natural-language requests to ORBIT tools.

    First version supports terminal execution only.
    """

    def __init__(self, terminal: Terminal) -> None:
        self.terminal = terminal

    def handle(self, text: str) -> ToolResult:
        command = self._detect_terminal_command(text)

        if not command:
            return ToolResult(handled=False)

        try:
            result = self.terminal.run_safe(command)
        except Exception as exc:
            warn(str(exc))
            return ToolResult(handled=True)

        console.print(f"[bold cyan]Command:[/bold cyan] {result.command}")
        console.print(f"[bold cyan]Exit code:[/bold cyan] {result.exit_code}")

        if result.stdout:
            console.print(
                Panel(
                    result.stdout,
                    title="stdout",
                    border_style="green",
                )
            )

        if result.stderr:
            console.print(
                Panel(
                    result.stderr,
                    title="stderr",
                    border_style="red",
                )
            )

        return ToolResult(handled=True)

    def _detect_terminal_command(self, text: str) -> str | None:
        value = text.strip()

        lowered = value.lower()

        shortcuts = {
            "git status": "git status",
            "show git status": "git status",
            "run git status": "git status",
            "git diff": "git diff",
            "show git diff": "git diff",
            "run tests": "pytest",
            "run pytest": "pytest",
            "pytest": "pytest",
            "list files": "ls",
            "show files": "ls",
            "where am i": "pwd",
            "pwd": "pwd",
        }

        if lowered in shortcuts:
            return shortcuts[lowered]

        patterns = [
            r"^run\s+(.+)$",
            r"^execute\s+(.+)$",
        ]

        for pattern in patterns:
            match = re.match(pattern, value, flags=re.IGNORECASE)

            if match:
                return match.group(1).strip()

        return None