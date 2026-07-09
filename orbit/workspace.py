from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from difflib import unified_diff


class Workspace:
    """
    Safe filesystem operations for ORBIT.

    This class never talks to the LLM.
    It only performs file operations.
    """

    def __init__(self, workspace: str | Path) -> None:
        self.workspace = Path(workspace).resolve()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _resolve(self, path: str | Path) -> Path:
        """
        Resolve a path inside the workspace.

        Prevents writing outside the project.
        """

        target = (self.workspace / path).resolve()

        if not str(target).startswith(str(self.workspace)):
            raise ValueError("Path escapes workspace.")

        return target

    # ------------------------------------------------------------------
    # Information
    # ------------------------------------------------------------------

    def exists(self, path: str | Path) -> bool:
        return self._resolve(path).exists()

    def is_file(self, path: str | Path) -> bool:
        return self._resolve(path).is_file()

    def is_directory(self, path: str | Path) -> bool:
        return self._resolve(path).is_dir()

    def list_directory(self, path: str | Path = ".") -> list[str]:
        directory = self._resolve(path)

        return sorted(
            item.name
            for item in directory.iterdir()
        )

    # ------------------------------------------------------------------
    # Reading
    # ------------------------------------------------------------------

    def read_file(
        self,
        path: str | Path,
        encoding: str = "utf-8",
    ) -> str:

        return self._resolve(path).read_text(
            encoding=encoding,
        )

    # ------------------------------------------------------------------
    # Writing
    # ------------------------------------------------------------------

    def write_file(
        self,
        path: str | Path,
        content: str,
        encoding: str = "utf-8",
    ) -> None:

        target = self._resolve(path)

        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        target.write_text(
            content,
            encoding=encoding,
        )

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create_file(
        self,
        path: str | Path,
        content: str = "",
    ) -> None:

        target = self._resolve(path)

        if target.exists():
            raise FileExistsError(path)

        self.write_file(path, content)

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete_file(
        self,
        path: str | Path,
    ) -> None:

        target = self._resolve(path)

        if not target.exists():
            raise FileNotFoundError(path)

        target.unlink()

    # ------------------------------------------------------------------
    # Rename
    # ------------------------------------------------------------------

    def rename_file(
        self,
        old: str | Path,
        new: str | Path,
    ) -> None:

        src = self._resolve(old)
        dst = self._resolve(new)

        dst.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        src.rename(dst)

    # ------------------------------------------------------------------
    # Copy
    # ------------------------------------------------------------------

    def copy_file(
        self,
        src: str | Path,
        dst: str | Path,
    ) -> None:

        shutil.copy2(
            self._resolve(src),
            self._resolve(dst),
        )

    # ------------------------------------------------------------------
    # Move
    # ------------------------------------------------------------------

    def move_file(
        self,
        src: str | Path,
        dst: str | Path,
    ) -> None:

        shutil.move(
            str(self._resolve(src)),
            str(self._resolve(dst)),
        )

    # ------------------------------------------------------------------
    # Backup
    # ------------------------------------------------------------------

    def backup_file(
        self,
        path: str | Path,
    ) -> Path:

        target = self._resolve(path)

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        backup = target.with_suffix(
            target.suffix + f".{timestamp}.bak"
        )

        shutil.copy2(target, backup)

        return backup

    # ------------------------------------------------------------------
    # Restore
    # ------------------------------------------------------------------

    def restore_backup(
        self,
        backup: str | Path,
        destination: str | Path,
    ) -> None:

        shutil.copy2(
            self._resolve(backup),
            self._resolve(destination),
        )

    # ------------------------------------------------------------------
    # Append
    # ------------------------------------------------------------------

    def append_text(
        self,
        path: str | Path,
        text: str,
        encoding: str = "utf-8",
    ) -> None:

        target = self._resolve(path)

        with target.open(
            "a",
            encoding=encoding,
        ) as file:

            file.write(text)

    # ------------------------------------------------------------------
    # Replace
    # ------------------------------------------------------------------

    def replace_text(
        self,
        path: str | Path,
        old: str,
        new: str,
    ) -> bool:

        content = self.read_file(path)

        if old not in content:
            return False

        content = content.replace(old, new)

        self.write_file(path, content)

        return True

    # ------------------------------------------------------------------
    # Diff
    # ------------------------------------------------------------------

    def show_diff(
        self,
        original: str,
        updated: str,
        filename: str = "file",
    ) -> str:

        diff = unified_diff(
            original.splitlines(),
            updated.splitlines(),
            fromfile=filename,
            tofile=filename,
            lineterm="",
        )

        return "\n".join(diff)