from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from rich.panel import Panel
from rich.prompt import Confirm

from .chat import ChatSession
from .editor import EditProposal, Editor
from .planner import Planner
from .terminal import Terminal
from .ui import console, ok, warn
from .validator import ValidationCommand, Validator


DEFAULT_MAX_REPAIR_ATTEMPTS = 2


@dataclass
class AgentResult:
    success: bool
    message: str = ""


@dataclass
class ValidationResult:
    success: bool
    command: str
    output: str
    exit_code: int | None
    message: str = ""


class Agent:
    """
    High-level AI workflows.

    Coordinates planning, AI-generated edits, file updates,
    cross-language validation, and controlled repair attempts.
    """

    def __init__(
        self,
        chat: ChatSession,
        editor: Editor,
        planner: Planner,
        terminal: Terminal,
        validator: Validator,
    ) -> None:
        self.chat = chat
        self.editor = editor
        self.planner = planner
        self.terminal = terminal
        self.validator = validator

    def edit_request(
        self,
        instruction: str,
    ) -> AgentResult:
        """
        Plan and apply coordinated edits across one or more files.
        """

        plan = self.planner.plan_request(instruction)

        if not plan.steps:
            return AgentResult(False, "No suitable files found.")

        console.print("\n[bold cyan]Execution Plan[/bold cyan]")
        console.print(f"[bold]Objective:[/bold] {plan.objective}\n")

        for step in plan.steps:
            console.print(f"• {step.path} - {step.reason}")

        if not Confirm.ask("\nProceed with this plan?"):
            return AgentResult(False, "Cancelled.")

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
            return AgentResult(True, "No changes required.")

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
            return AgentResult(False, "Cancelled.")

        try:
            self.editor.apply_proposals(proposals)
        except Exception as exc:
            warn(str(exc))
            return AgentResult(False, str(exc))

        for proposal in proposals:
            ok(f"Updated {proposal.path}")

        changed_paths = [proposal.path for proposal in proposals]

        validation_result = self.validate_and_repair(
            instruction=instruction,
            paths=changed_paths,
            original_proposals=proposals,
        )

        if not validation_result.success:
            return validation_result

        return AgentResult(
            True,
            (
                f"Applied and validated changes to "
                f"{len(proposals)} file(s)."
            ),
        )

    def edit_file(
        self,
        path: str | Path,
        instruction: str,
    ) -> AgentResult:
        """
        Generate an AI edit, preview the diff,
        apply it, validate it, and repair it when necessary.
        """

        path_string = str(path)

        plan = self.planner.plan_edit(
            path_string,
            instruction,
        )

        console.print("\n[bold cyan]Execution Plan[/bold cyan]")
        console.print(f"[bold]Objective:[/bold] {plan.objective}\n")

        for step in plan.steps:
            console.print(f"• {step.path} - {step.reason}")

        if not Confirm.ask("\nProceed with this plan?"):
            return AgentResult(False, "Cancelled.")

        try:
            original = self.editor.read_file(path)
        except Exception as exc:
            return AgentResult(
                False,
                f"Could not read {path}: {exc}",
            )

        try:
            updated = self.chat.generate_file_edit(
                path_string,
                original,
                instruction,
            )
        except Exception as exc:
            return AgentResult(
                False,
                f"Could not generate edit for {path}: {exc}",
            )

        if not updated:
            return AgentResult(False, "Model returned no edit.")

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
            return AgentResult(True, "No changes required.")

        if not Confirm.ask("Apply changes?"):
            return AgentResult(False, "Cancelled.")

        try:
            self.editor.apply_changes(
                path,
                proposal.new_content,
            )
        except Exception as exc:
            return AgentResult(
                False,
                f"Could not apply changes to {proposal.path}: {exc}",
            )

        ok(f"Updated {proposal.path}")

        validation_result = self.validate_and_repair(
            instruction=instruction,
            paths=[proposal.path],
            original_proposals=[proposal],
        )

        if not validation_result.success:
            return validation_result

        return AgentResult(True, "Applied and validated.")

    def validate_command(
        self,
        validation_command: ValidationCommand,
    ) -> ValidationResult:
        """
        Run one safe validation command and preserve its full result.
        """

        command = validation_command.command

        try:
            result = self.terminal.run_safe(command)
        except Exception as exc:
            message = f"Validation could not run: {exc}"

            console.print(
                Panel(
                    message,
                    title=(
                        f"Validation: "
                        f"{validation_command.description}"
                    ),
                    border_style="red",
                )
            )

            return ValidationResult(
                success=False,
                command=command,
                output=message,
                exit_code=None,
                message=message,
            )

        output_parts = []

        if result.stdout.strip():
            output_parts.append(result.stdout.strip())

        if result.stderr.strip():
            output_parts.append(result.stderr.strip())

        output = "\n\n".join(output_parts) or "No output."

        console.print(
            Panel(
                output,
                title=(
                    f"Validation: "
                    f"{validation_command.description}"
                ),
                subtitle=command,
                border_style=(
                    "green"
                    if result.success
                    else "red"
                ),
            )
        )

        if not result.success:
            return ValidationResult(
                success=False,
                command=command,
                output=output,
                exit_code=result.exit_code,
                message=(
                    f"Validation failed with exit code "
                    f"{result.exit_code}."
                ),
            )

        return ValidationResult(
            success=True,
            command=command,
            output=output,
            exit_code=result.exit_code,
            message="Validation passed.",
        )

    def validate_and_repair(
        self,
        instruction: str,
        paths: list[str],
        original_proposals: list[EditProposal],
        max_attempts: int = DEFAULT_MAX_REPAIR_ATTEMPTS,
    ) -> AgentResult:
        """
        Run all applicable validators and repair failing files.
        """

        commands = self.validator.build_commands(paths)
        unsupported = self.validator.unsupported_paths(paths)

        if unsupported:
            warn(
                "No automatic validator configured for: "
                + ", ".join(unsupported)
            )

        if not commands:
            return AgentResult(
                True,
                (
                    "Changes applied, but no automatic validator "
                    "was available for the changed file types."
                ),
            )

        for validation_command in commands:
            validation = self.validate_command(validation_command)

            if validation.success:
                continue

            if validation.exit_code is None:
                return self._rollback_after_failure(
                    original_proposals,
                    validation.message,
                )

            repair_result = self._repair_failed_validation(
                instruction=instruction,
                validation_command=validation_command,
                validation=validation,
                max_attempts=max_attempts,
            )

            if not repair_result.success:
                return self._rollback_after_failure(
                    original_proposals,
                    repair_result.message,
                )

        return AgentResult(
            True,
            "All available validation commands passed.",
        )

    def _rollback_after_failure(
        self,
        original_proposals: list[EditProposal],
        failure_message: str,
    ) -> AgentResult:
        """
        Restore the original file contents after validation or repair fails.
        """

        warn(failure_message)
        warn("Validation failed. Rolling back original changes.")

        try:
            self.editor.restore_proposals(original_proposals)
        except Exception as exc:
            return AgentResult(
                False,
                (
                    f"{failure_message} "
                    f"Automatic rollback also failed: {exc}"
                ),
            )

        for proposal in original_proposals:
            ok(f"Restored {proposal.path}")

        rollback_paths = [
            proposal.path
            for proposal in original_proposals
        ]

        commands = self.validator.build_commands(rollback_paths)
        rollback_validation_failures: list[str] = []

        for validation_command in commands:
            result = self.validate_command(validation_command)

            if not result.success:
                rollback_validation_failures.append(
                    f"{validation_command.description}: "
                    f"{result.message}"
                )

        if rollback_validation_failures:
            details = "; ".join(rollback_validation_failures)

            return AgentResult(
                False,
                (
                    f"{failure_message} Original files were restored, "
                    f"but the restored state did not validate: {details}"
                ),
            )

        ok("Rollback completed successfully.")

        return AgentResult(
            False,
            (
                f"{failure_message} Original file contents were restored."
            ),
        )

    def _repair_failed_validation(
        self,
        instruction: str,
        validation_command: ValidationCommand,
        validation: ValidationResult,
        max_attempts: int,
    ) -> AgentResult:
        """
        Repair files associated with one failing validation command.
        """

        warn(validation.message)

        for attempt in range(1, max_attempts + 1):
            console.print(
                f"\n[bold yellow]Repair attempt "
                f"{attempt}/{max_attempts}[/bold yellow]"
            )

            repair_paths = self._select_repair_paths(
                validation_command.paths,
                validation.output,
            )

            repair_proposals = []

            for path in repair_paths:
                try:
                    current_content = self.editor.read_file(path)
                except Exception as exc:
                    return AgentResult(
                        False,
                        f"Could not read {path} for repair: {exc}",
                    )

                try:
                    repaired_content = self.chat.generate_repair_edit(
                        path=path,
                        current_content=current_content,
                        original_instruction=instruction,
                        validation_command=validation.command,
                        validation_output=validation.output,
                        attempt=attempt,
                        max_attempts=max_attempts,
                    )
                except Exception as exc:
                    return AgentResult(
                        False,
                        f"Could not generate repair for {path}: {exc}",
                    )

                if not repaired_content:
                    warn(f"Model returned no repair for {path}.")
                    continue

                try:
                    proposal = self.editor.propose_file_edit(
                        path,
                        repaired_content,
                    )
                except Exception as exc:
                    return AgentResult(
                        False,
                        f"Could not prepare repair diff for {path}: {exc}",
                    )

                if proposal.original_content != proposal.new_content:
                    repair_proposals.append(proposal)

            if not repair_proposals:
                return AgentResult(
                    False,
                    (
                        "Validation failed and the model produced "
                        "no repair changes."
                    ),
                )

            for proposal in repair_proposals:
                console.print(
                    Panel(
                        proposal.diff or "No changes.",
                        title=(
                            f"Repair Diff {attempt}/{max_attempts}: "
                            f"{proposal.path}"
                        ),
                        border_style="yellow",
                    )
                )

            if not Confirm.ask(
                (
                    f"Apply repair attempt {attempt} to "
                    f"{len(repair_proposals)} file(s)?"
                )
            ):
                return AgentResult(False, "Repair cancelled.")

            try:
                self.editor.apply_proposals(repair_proposals)
            except Exception as exc:
                return AgentResult(
                    False,
                    f"Could not apply repair: {exc}",
                )

            for proposal in repair_proposals:
                ok(f"Repaired {proposal.path}")

            validation = self.validate_command(
                validation_command
            )

            if validation.success:
                ok(
                    f"Validation passed after repair "
                    f"attempt {attempt}."
                )

                return AgentResult(
                    True,
                    (
                        f"Validation passed after "
                        f"{attempt} repair attempt(s)."
                    ),
                )

            warn(validation.message)

        return AgentResult(
            False,
            (
                f"Validation still failed after "
                f"{max_attempts} repair attempts."
            ),
        )

    def _select_repair_paths(
        self,
        paths: list[str],
        validation_output: str,
    ) -> list[str]:
        """
        Prefer changed files explicitly named in validation output.

        If no path is mentioned, repair all files tied to the command.
        """

        normalized_output = validation_output.replace("\\", "/")

        mentioned_paths = [
            path
            for path in paths
            if path.replace("\\", "/") in normalized_output
        ]

        return mentioned_paths or paths
