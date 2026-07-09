from __future__ import annotations

from pathlib import Path

from .workspace import Workspace


class Editor:
    """
    High-level editing operations.

    This class sits above Workspace and will later coordinate
    AI-generated edits, diffs, confirmations, and file writes.
    """

    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

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