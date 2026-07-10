from __future__ import annotations

from pathlib import Path

from .workspace import Workspace
from dataclasses import dataclass


@dataclass
class EditProposal:
    path: str
    original_content: str
    new_content: str
    diff: str


class Editor:
    """
    High-level editing operations.

    This class sits above Workspace and will later coordinate
    AI-generated edits, diffs, confirmations, and file writes.
    """

    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace


    
    # ------------------------------------------------------------------
    # Apply Multiple
    # ------------------------------------------------------------------

    def apply_proposals(
        self,
        proposals: list[EditProposal],
    ) -> None:
        """
        Apply multiple edit proposals transactionally.

        If any write fails, all previously modified files are restored
        to their original contents.
        """

        applied: list[EditProposal] = []

        try:
            for proposal in proposals:
                self.workspace.write_file(
                    proposal.path,
                    proposal.new_content,
                )

                applied.append(proposal)

        except Exception as exc:
            rollback_errors: list[str] = []

            for proposal in reversed(applied):
                try:
                    self.workspace.write_file(
                        proposal.path,
                        proposal.original_content,
                    )
                except Exception as rollback_exc:
                    rollback_errors.append(
                        f"{proposal.path}: {rollback_exc}"
                    )

            if rollback_errors:
                details = "; ".join(rollback_errors)

                raise RuntimeError(
                    f"Multi-file edit failed: {exc}. "
                    f"Rollback also failed for: {details}"
                ) from exc

            raise RuntimeError(
                f"Multi-file edit failed and was rolled back: {exc}"
            ) from exc


    # ------------------------------------------------------------------
    # Propose File Edit
    # ------------------------------------------------------------------
    def propose_file_edit(
        self,
        path: str | Path,
        new_content: str,
    ) -> EditProposal:
        """
        Build an edit proposal without modifying the file.
        """

        original = self.workspace.read_file(path)

        diff = self.workspace.show_diff(
            original,
            new_content,
            filename=str(path),
        )

        return EditProposal(
            path=str(path),
            original_content=original,
            new_content=new_content,
            diff=diff,
        )

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def read_file(self, path: str | Path) -> str:
        return self.workspace.read_file(path)

    # ------------------------------------------------------------------
    # Edit
    # ------------------------------------------------------------------

    def edit_file(
        self,
        path: str | Path,
        new_content: str,
        backup: bool = True,
    ) -> None:
        """
        Replace an entire file.
        """

        if backup and self.workspace.exists(path):
            self.workspace.backup_file(path)

        self.workspace.write_file(path, new_content)

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create_file(
        self,
        path: str | Path,
        content: str = "",
    ) -> None:
        self.workspace.create_file(path, content)

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete_file(
        self,
        path: str | Path,
        backup: bool = True,
    ) -> None:
        """
        Delete a file, optionally backing it up first.
        """

        if backup and self.workspace.exists(path):
            self.workspace.backup_file(path)

        self.workspace.delete_file(path)

    # ------------------------------------------------------------------
    # Replace Text
    # ------------------------------------------------------------------

    def replace_text(
        self,
        path: str | Path,
        old: str,
        new: str,
        backup: bool = True,
    ) -> bool:
        """
        Replace text inside a file.
        """

        if backup and self.workspace.exists(path):
            self.workspace.backup_file(path)

        return self.workspace.replace_text(path, old, new)

    # ------------------------------------------------------------------
    # Diff
    # ------------------------------------------------------------------

    def preview_changes(
        self,
        path: str | Path,
        new_content: str,
    ) -> str:
        """
        Generate a unified diff without modifying the file.
        """

        original = self.workspace.read_file(path)

        return self.workspace.show_diff(
            original,
            new_content,
            filename=str(path),
        )

    # ------------------------------------------------------------------
    # Apply
    # ------------------------------------------------------------------

    def apply_changes(
        self,
        path: str | Path,
        new_content: str,
        backup: bool = True,
    ) -> None:
        """
        Apply a full-file replacement.
        """

        self.edit_file(
            path,
            new_content,
            backup=backup,
        )