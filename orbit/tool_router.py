from __future__ import annotations

import re
from dataclasses import dataclass

from rich.panel import Panel
from rich.prompt import Confirm

from .editor import Editor
from .terminal import Terminal
from .ui import console, ok, warn


@dataclass
class ToolResult:
    handled: bool


class ToolRouter:
    """
    Routes simple natural-language requests to ORBIT tools.
    """

    def __init__(
        self,
        terminal: Terminal,
        editor: Editor,
    ) -> None:
        self.terminal = terminal
        self.editor = editor

    def handle(self, text: str) -> ToolResult:
        if self._handle_workspace_action(text):
            return ToolResult(handled=True)

        command = self._detect_terminal_command(text)

        if command:
            self._run_terminal(command)
            return ToolResult(handled=True)

        return ToolResult(handled=False)

    # ------------------------------------------------------------------
    # Workspace actions
    # ------------------------------------------------------------------

    def _handle_workspace_action(self, text: str) -> bool:
        value = text.strip()

        # ---------------------------------------------------------
        # Create
        # ---------------------------------------------------------

        create_match = re.match(
            r"^(create|new)\s+([A-Za-z0-9_./\\-]+)$",
            value,
            flags=re.IGNORECASE,
        )

        if create_match:
            path = create_match.group(2)

            if Confirm.ask(f"Create {path}?"):
                try:
                    self.editor.create_file(path)
                    ok(f"Created {path}")
                except FileExistsError:
                    warn(f"File already exists: {path}")
                except Exception as exc:
                    warn(str(exc))

            return True

        # ---------------------------------------------------------
        # Delete
        # ---------------------------------------------------------

        delete_match = re.match(
            r"^(delete|remove)\s+([A-Za-z0-9_./\\-]+)$",
            value,
            flags=re.IGNORECASE,
        )

        if delete_match:
            path = delete_match.group(2)

            if Confirm.ask(f"Delete {path}?"):
                try:
                    self.editor.delete_file(path)
                    ok(f"Deleted {path}")
                except FileNotFoundError:
                    warn(f"File not found: {path}")
                except Exception as exc:
                    warn(str(exc))

            return True

        # ---------------------------------------------------------
        # Rename
        # ---------------------------------------------------------

        rename_match = re.match(
            r"^rename\s+([A-Za-z0-9_./\\-]+)\s+to\s+([A-Za-z0-9_./\\-]+)$",
            value,
            flags=re.IGNORECASE,
        )

        if rename_match:
            old = rename_match.group(1)
            new = rename_match.group(2)

            if Confirm.ask(f"Rename {old} to {new}?"):
                try:
                    self.editor.workspace.rename_file(old, new)
                    ok(f"Renamed {old} to {new}")
                except FileNotFoundError:
                    warn(f"File not found: {old}")
                except FileExistsError:
                    warn(f"Destination already exists: {new}")
                except Exception as exc:
                    warn(str(exc))

            return True

        # ---------------------------------------------------------
        # Copy
        # ---------------------------------------------------------

        copy_match = re.match(
            r"^copy\s+([A-Za-z0-9_./\\-]+)\s+to\s+([A-Za-z0-9_./\\-]+)$",
            value,
            flags=re.IGNORECASE,
        )

        if copy_match:
            src = copy_match.group(1)
            dst = copy_match.group(2)

            if Confirm.ask(f"Copy {src} to {dst}?"):
                try:
                    self.editor.workspace.copy_file(src, dst)
                    ok(f"Copied {src} to {dst}")
                except FileNotFoundError:
                    warn(f"File not found: {src}")
                except FileExistsError:
                    warn(f"Destination already exists: {dst}")
                except Exception as exc:
                    warn(str(exc))

            return True

        # ---------------------------------------------------------
        # Move
        # ---------------------------------------------------------

        move_match = re.match(
            r"^move\s+([A-Za-z0-9_./\\-]+)\s+to\s+([A-Za-z0-9_./\\-]+)$",
            value,
            flags=re.IGNORECASE,
        )

        if move_match:
            src = move_match.group(1)
            dst = move_match.group(2)

            if Confirm.ask(f"Move {src} to {dst}?"):
                try:
                    self.editor.workspace.move_file(src, dst)
                    ok(f"Moved {src} to {dst}")
                except FileNotFoundError:
                    warn(f"File not found: {src}")
                except FileExistsError:
                    warn(f"Destination already exists: {dst}")
                except Exception as exc:
                    warn(str(exc))

            return True

        return False

    # ------------------------------------------------------------------
    # Terminal actions
    # ------------------------------------------------------------------

    def _run_terminal(self, command: str) -> None:
        try:
            result = self.terminal.run_safe(command)
        except Exception as exc:
            warn(str(exc))
            return

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