from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


from rich.prompt import Confirm
from rich.panel import Panel

from .chat import ChatSession
from .editor import Editor
from .planner import Planner
from .ui import console, ok, warn


@dataclass
class AgentResult:
    success: bool
    message: str = ""


class Agent:
    """
    High-level AI workflows.

    Coordinates ChatSession + Editor.
    """

    def __init__(
        self,
        chat: ChatSession,
        editor: Editor,
        planner: Planner,
    ) -> None:
        self.chat = chat
        self.editor = editor
        self.planner = planner

    def edit_file(
        self,
        path: str | Path,
        instruction: str,
    ) -> AgentResult:
        """
        Generate an AI edit, preview the diff,
        and optionally apply it.
        """
        plan = self.planner.plan_edit(
            str(path),
            instruction,
        )

        console.print("\n[bold cyan]Execution Plan[/bold cyan]")

        console.print(f"[bold]Objective:[/bold] {plan.objective}\n")

        for step in plan.steps:
            console.print(
                f"• {step.path} - {step.reason}"
            )

        if not Confirm.ask("\nProceed with this plan?"):
            return AgentResult(
                False,
                "Cancelled.",
            )
        try:
            original = self.editor.read_file(path)
        except Exception as exc:
            return AgentResult(False, str(exc))

        updated = self.chat.generate_file_edit(
            str(path),
            original,
            instruction,
        )

        if not updated:
            return AgentResult(False, "Model returned no edit.")

        proposal = self.editor.propose_file_edit(
            path,
            updated,
        )

        console.print(
            Panel(
                proposal.diff or "No changes.",
                title=f"Diff: {proposal.path}",
                border_style="cyan",
            )
        )

        if proposal.original_content == proposal.new_content:
            return AgentResult(
                True,
                "No changes required.",
            )

        if not Confirm.ask("Apply changes?"):
            return AgentResult(
                False,
                "Cancelled.",
            )

        self.editor.apply_changes(
            path,
            proposal.new_content,
        )

        ok(f"Updated {proposal.path}")

        return AgentResult(
            True,
            "Applied.",
        )