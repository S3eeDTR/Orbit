
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from rich.panel import Panel
from rich.prompt import Confirm

from .chat import ChatSession
from .editor import Editor
from .planner import Planner
from .terminal import Terminal
from .ui import console, ok, warn


@dataclass
class AgentResult:
    success: bool
    message: str = ""


class Agent:
    """
    High-level AI workflows.

    Coordinates planning, AI-generated edits, file updates,
    and post-edit validation.
    """

    def __init__(
        self,
        chat: ChatSession,
        editor: Editor,
        planner: Planner,
        terminal: Terminal,
    ) -> None:
        self.chat = chat
        self.editor = editor
        self.planner = planner
        self.terminal = terminal

    def edit_request(
        self,
        instruction: str,
    ) -> AgentResult:
        """
        Plan and apply coordinated edits across one or more files.
        """

        plan = self.planner.plan_request(instruction)

        if not plan.steps:
            return AgentResult(
                False,
                "No suitable files found.",
            )

        console.print("\n[bold cyan]Execution Plan[/bold cyan]")
        console.print(
            f"[bold]Objective:[/bold] {plan.objective}\n"
        )

        for step in plan.steps:
            console.print(
                f"• {step.path} - {step.reason}"
            )

        if not Confirm.ask("\nProceed with this plan?"):
            return AgentResult(
                False,
                "Cancelled.",
            )

        proposals = []

        for step in plan.steps:
            try:
                original = self.editor.read_file(step.path)
            except Exception as exc:
                return AgentResult(
                    False,
                    f"Could not read {step.path}: {exc}",
                )

            try:
                updated = self.chat.generate_file_edit(
                    step.path,
                    original,
                    instruction,
                )
            except Exception as exc:
                return AgentResult(
                    False,
                    f"Could not generate edit for {step.path}: {exc}",
                )

            if not updated:
                return AgentResult(
                    False,
                    f"Model returned no edit for {step.path}.",
                )

            try:
                proposal = self.editor.propose_file_edit(
                    step.path,
                    updated,
                )
            except Exception as exc:
                return AgentResult(
                    False,
                    f"Could not prepare diff for {step.path}: {exc}",
                )

            if proposal.original_content != proposal.new_content:
                proposals.append(proposal)

        if not proposals:
            return AgentResult(
                True,
                "No changes required.",
            )

        for proposal in proposals:
            console.print(
                Panel(
                    proposal.diff or "No changes.",
                    title=f"Diff: {proposal.path}",
                    border_style="cyan",
                )
            )

        if not Confirm.ask(
            f"Apply changes to {len(proposals)} file(s)?"
        ):
            return AgentResult(
                False,
                "Cancelled.",
            )

        try:
            self.editor.apply_proposals(proposals)
        except Exception as exc:
            warn(str(exc))

            return AgentResult(
                False,
                str(exc),
            )

        for proposal in proposals:
            ok(f"Updated {proposal.path}")

        validation = self.validate_changes()

        if not validation.success:
            warn(validation.message)

            return AgentResult(
                False,
                (
                    f"Applied changes to {len(proposals)} file(s), "
                    "but validation failed."
                ),
            )

        return AgentResult(
            True,
            (
                f"Applied and validated changes to "
                f"{len(proposals)} file(s)."
            ),
        )

    def validate_changes(
        self,
        command: str = "python -m compileall orbit",
    ) -> AgentResult:
        """
        Run a safe validation command after applying edits.
        """

        try:
            result = self.terminal.run_safe(command)
        except Exception as exc:
            return AgentResult(
                False,
                f"Validation could not run: {exc}",
            )

        output = result.stdout or result.stderr or "No output."

        console.print(
            Panel(
                output,
                title=f"Validation: {command}",
                border_style=(
                    "green"
                    if result.exit_code == 0
                    else "red"
                ),
            )
        )

        if result.exit_code != 0:
            return AgentResult(
                False,
                (
                    f"Validation failed with exit code "
                    f"{result.exit_code}."
                ),
            )

        return AgentResult(
            True,
            "Validation passed.",
        )

    def edit_file(
        self,
        path: str | Path,
        instruction: str,
    ) -> AgentResult:
        """
        Generate an AI edit, preview the diff,
        apply it, and validate the result.
        """

        plan = self.planner.plan_edit(
            str(path),
            instruction,
        )

        console.print("\n[bold cyan]Execution Plan[/bold cyan]")
        console.print(
            f"[bold]Objective:[/bold] {plan.objective}\n"
        )

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
            return AgentResult(
                False,
                f"Could not read {path}: {exc}",
            )

        try:
            updated = self.chat.generate_file_edit(
                str(path),
                original,
                instruction,
            )
        except Exception as exc:
            return AgentResult(
                False,
                f"Could not generate edit for {path}: {exc}",
            )

        if not updated:
            return AgentResult(
                False,
                "Model returned no edit.",
            )

        try:
            proposal = self.editor.propose_file_edit(
                path,
                updated,
            )
        except Exception as exc:
            return AgentResult(
                False,
                f"Could not prepare diff for {path}: {exc}",
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

        try:
            self.editor.apply_changes(
                path,
                proposal.new_content,
            )
        except Exception as exc:
            return AgentResult(
                False,
                (
                    f"Could not apply changes to "
                    f"{proposal.path}: {exc}"
                ),
            )

        ok(f"Updated {proposal.path}")

        validation = self.validate_changes()

        if not validation.success:
            warn(validation.message)

            return AgentResult(
                False,
                (
                    f"Updated {proposal.path}, "
                    "but validation failed."
                ),
            )

        return AgentResult(
            True,
            "Applied and validated.",
        )