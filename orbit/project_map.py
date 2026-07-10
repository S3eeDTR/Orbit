from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .chat import ChatSession
from .project import ProjectInfo
from .workspace import Workspace


@dataclass
class ProjectMapEntry:
    path: str
    description: str
    file_hash: str
    last_modified: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "summary": self.description,
            "file_hash": self.file_hash,
            "last_modified": self.last_modified,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProjectMapEntry:
        return cls(
            path=str(data["path"]),
            description=str(
                data.get("summary")
                or data.get("description")
                or "Project source file."
            ),
            file_hash=str(data.get("file_hash", "")),
            last_modified=float(data.get("last_modified", 0.0)),
        )


class ProjectMap:
    """
    Builds and maintains ORBIT's persistent semantic project index.
    """

    INDEX_VERSION = 1

    def __init__(
        self,
        project: ProjectInfo,
        workspace: Workspace,
        chat: ChatSession,
        max_file_chars: int = 4000,
        index_path: str = ".orbit/project_map.json",
    ) -> None:
        self.project = project
        self.workspace = workspace
        self.chat = chat
        self.max_file_chars = max_file_chars

        self.project_root = self._resolve_project_root()
        self.index_path = self.project_root / index_path

    def build(self, limit: int = 80) -> list[ProjectMapEntry]:
        """
        Return cached project-map entries for the planner.

        If no index exists yet, create one once. Subsequent planner runs
        load the cached index without calling the LLM again.
        """
        entries = self.load()

        if not entries:
            entries = self.index()

        return entries[:limit]

    def index(
        self,
        *,
        refresh: bool = False,
        changed_only: bool = False,
        limit: int | None = None,
    ) -> list[ProjectMapEntry]:
        """
        Create or update the persistent project index.

        refresh:
            Rebuild every entry, ignoring the existing cache.

        changed_only:
            Only summarize new or modified files. Unchanged cached entries
            are preserved, and deleted files are removed.

        Default:
            Incrementally updates new and modified files.
        """
        existing_entries = [] if refresh else self.load()
        existing_by_path = {
            entry.path: entry
            for entry in existing_entries
        }

        project_files = list(self.project.files)

        if limit is not None:
            project_files = project_files[:limit]

        updated_entries: list[ProjectMapEntry] = []

        for path in project_files:
            try:
                file_hash = self.calculate_hash(path)
                last_modified = self.get_last_modified(path)
            except Exception:
                continue

            cached_entry = existing_by_path.get(path)

            is_unchanged = (
                cached_entry is not None
                and cached_entry.file_hash == file_hash
            )

            if not refresh and is_unchanged:
                updated_entries.append(cached_entry)
                continue

            if changed_only or refresh or cached_entry is None:
                description = self.describe_file(path)

                updated_entries.append(
                    ProjectMapEntry(
                        path=path,
                        description=description,
                        file_hash=file_hash,
                        last_modified=last_modified,
                    )
                )
                continue

            description = self.describe_file(path)

            updated_entries.append(
                ProjectMapEntry(
                    path=path,
                    description=description,
                    file_hash=file_hash,
                    last_modified=last_modified,
                )
            )

        self.save(updated_entries)
        return updated_entries

    def load(self) -> list[ProjectMapEntry]:
        """
        Load cached project-map entries.

        Returns an empty list when the index does not exist or is invalid.
        """
        if not self.index_path.exists():
            return []

        try:
            data = json.loads(
                self.index_path.read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError):
            return []

        if not isinstance(data, dict):
            return []

        files = data.get("files", [])

        if not isinstance(files, list):
            return []

        entries: list[ProjectMapEntry] = []

        for item in files:
            if not isinstance(item, dict):
                continue

            try:
                entries.append(ProjectMapEntry.from_dict(item))
            except (KeyError, TypeError, ValueError):
                continue

        return entries

    def save(self, entries: list[ProjectMapEntry]) -> None:
        """
        Persist the project map using an atomic file replacement.
        """
        self.index_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        payload = {
            "version": self.INDEX_VERSION,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "files": [
                entry.to_dict()
                for entry in sorted(
                    entries,
                    key=lambda item: item.path,
                )
            ],
        }

        temporary_path = self.index_path.with_suffix(".json.tmp")

        temporary_path.write_text(
            json.dumps(
                payload,
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )

        temporary_path.replace(self.index_path)

    def calculate_hash(self, path: str) -> str:
        """
        Calculate a SHA-256 hash from the file's current contents.
        """
        content = self.workspace.read_file(path)

        digest = hashlib.sha256(
            content.encode(
                "utf-8",
                errors="replace",
            )
        ).hexdigest()

        return f"sha256:{digest}"

    def get_last_modified(self, path: str) -> float:
        """
        Return the file modification timestamp when available.
        """
        absolute_path = self.project_root / path

        try:
            return absolute_path.stat().st_mtime
        except OSError:
            return 0.0

    def describe_file(self, path: str) -> str:
        try:
            content = self.workspace.read_file(path)
        except Exception:
            return "Unable to read file."

        if len(content) > self.max_file_chars:
            content = (
                content[: self.max_file_chars]
                + "\n...[truncated]..."
            )

        prompt = f"""
You are ORBIT's project indexing engine.

Your task is to summarize ONE source code file.

File path:
{path}

File content:

{content}

Write ONE concise sentence (10-25 words) describing the primary responsibility of this file.

Rules:
- Focus on the file's purpose, not its implementation.
- Mention the main responsibility only.
- Mention important components only if necessary.
- Do not explain individual functions or classes.
- Do not mention implementation details unless they are essential.
- Do not use markdown.
- Do not wrap the response in quotes.
- Do not say "This file" or "The file".
- Return ONLY the description.

Examples:
- Application startup and dependency initialization.
- Handles conversations with the OpenRouter API.
- Routes user requests to the appropriate tools.
- Provides file editing operations with diff previews.
- Maintains workspace file management utilities.
"""

        try:
            reply = self.chat.complete_once(prompt)
        except Exception:
            return "Project source file."

        if not reply:
            return "Project source file."

        description = reply.strip().replace("\n", " ")

        return description or "Project source file."

    def _resolve_project_root(self) -> Path:
        workspace_root = getattr(self.workspace, "workspace", None)

        if workspace_root is not None:
            return Path(workspace_root).resolve()

        project_root = getattr(self.project, "root", None)

        if project_root is not None:
            return Path(project_root).resolve()

        return Path.cwd().resolve()