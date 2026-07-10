from __future__ import annotations

import fnmatch
import shutil

from dataclasses import dataclass
from datetime import datetime
from difflib import unified_diff
from pathlib import Path

@dataclass
class SearchMatch:
    path: str
    line_number: int
    line: str


class Workspace:
    """
    Safe filesystem operations for ORBIT.

    This class never talks to the LLM.
    It only performs file operations.
    """

    def __init__(self, workspace: str | Path) -> None:
        self.workspace = Path(workspace).resolve()
    

    def _relative_path(self, path: Path) -> str:
        """
        Return a workspace-relative POSIX path.
        """
        return path.relative_to(self.workspace).as_posix()

    def _should_skip(self, path: Path) -> bool:
        """
        Skip generated, hidden, dependency, and version-control folders.
        """
        ignored_directories = {
            ".git",
            ".orbit",
            ".venv",
            "venv",
            "__pycache__",
            "node_modules",
            "build",
            "dist",
        }

        try:
            relative_parts = path.relative_to(self.workspace).parts
        except ValueError:
            return True

        return any(
            part in ignored_directories
            for part in relative_parts
        )

    def _is_text_file(self, path: Path) -> bool:
        """
        Perform a lightweight binary-file check.
        """
        try:
            sample = path.read_bytes()[:1024]
        except OSError:
            return False

        return b"\x00" not in sample
    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _resolve(self, path: str | Path) -> Path:
        """
        Resolve a path inside the workspace.

        Prevents writing outside the project.
        """

        target = (self.workspace / path).resolve()

        try:
            target.relative_to(self.workspace)
        except ValueError as exc:
            raise ValueError("Path escapes workspace.") from exc

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
    # Find Files
    # ------------------------------------------------------------------

    def find_files(
        self,
        pattern: str,
        limit: int = 100,
    ) -> list[str]:
        """
        Find files by filename, relative path, or glob pattern.

        Examples:
            planner
            *.py
            orbit/*map*
        """
        pattern = pattern.strip()

        if not pattern:
            return []

        lowered_pattern = pattern.lower()
        has_glob = any(
            character in pattern
            for character in "*?[]"
        )

        matches: list[str] = []

        for path in self.workspace.rglob("*"):
            if not path.is_file():
                continue

            if self._should_skip(path):
                continue

            relative = self._relative_path(path)
            relative_lower = relative.lower()
            name_lower = path.name.lower()

            if has_glob:
                matched = (
                    fnmatch.fnmatch(relative_lower, lowered_pattern)
                    or fnmatch.fnmatch(name_lower, lowered_pattern)
                )
            else:
                matched = (
                    lowered_pattern in relative_lower
                    or lowered_pattern in name_lower
                )

            if not matched:
                continue

            matches.append(relative)

            if len(matches) >= limit:
                break

        return sorted(matches)

    # ------------------------------------------------------------------
    # Search Text
    # ------------------------------------------------------------------

    def search_text(
        self,
        query: str,
        path: str | Path = ".",
        *,
        case_sensitive: bool = False,
        limit: int = 200,
    ) -> list[SearchMatch]:
        """
        Search text across workspace files and return matching lines.
        """
        query = query.strip()

        if not query:
            return []

        search_root = self._resolve(path)

        if not search_root.exists():
            raise FileNotFoundError(path)

        if search_root.is_file():
            candidates = [search_root]
        else:
            candidates = search_root.rglob("*")

        needle = query if case_sensitive else query.lower()
        matches: list[SearchMatch] = []

        for file_path in candidates:
            if not file_path.is_file():
                continue

            if self._should_skip(file_path):
                continue

            if not self._is_text_file(file_path):
                continue

            try:
                content = file_path.read_text(
                    encoding="utf-8",
                    errors="replace",
                )
            except OSError:
                continue

            for line_number, line in enumerate(
                content.splitlines(),
                start=1,
            ):
                haystack = line if case_sensitive else line.lower()

                if needle not in haystack:
                    continue

                matches.append(
                    SearchMatch(
                        path=self._relative_path(file_path),
                        line_number=line_number,
                        line=line.strip(),
                    )
                )

                if len(matches) >= limit:
                    return matches

        return matches

    # ------------------------------------------------------------------
    # Grep
    # ------------------------------------------------------------------

    def grep(
        self,
        query: str,
        path: str | Path = ".",
        *,
        case_sensitive: bool = False,
        limit: int = 200,
    ) -> list[SearchMatch]:
        """
        Alias for text search with file paths and line numbers.
        """
        return self.search_text(
            query,
            path,
            case_sensitive=case_sensitive,
            limit=limit,
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