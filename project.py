from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from .constants import PROJECT_INDEX_FILE, PROJECT_INSTRUCTIONS_FILE

IGNORE_DIRS = {
    ".git", ".venv", "venv", "env", "__pycache__", "node_modules", ".mypy_cache",
    ".pytest_cache", "dist", "build", ".idea", ".vscode", ".next", ".cache"
}
TEXT_EXTS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".yaml", ".yml", ".toml",
    ".md", ".txt", ".html", ".css", ".scss", ".sh", ".ps1", ".sql", ".env.example"
}


@dataclass
class ProjectInfo:
    root: Path
    files: list[str] = field(default_factory=list)

    @property
    def file_count(self) -> int:
        return len(self.files)


def project_root(start: Path | None = None) -> Path:
    path = (start or Path.cwd()).resolve()
    for parent in [path, *path.parents]:
        if (parent / ".git").exists() or (parent / PROJECT_INSTRUCTIONS_FILE).exists():
            return parent
    return path


def should_include(path: Path) -> bool:
    if any(part in IGNORE_DIRS for part in path.parts):
        return False
    if path.name == PROJECT_INDEX_FILE:
        return False
    return path.is_file() and path.suffix.lower() in TEXT_EXTS


def scan_project(root: Path, max_files: int = 500) -> ProjectInfo:
    files: list[str] = []
    for path in root.rglob("*"):
        if len(files) >= max_files:
            break
        if should_include(path):
            try:
                files.append(str(path.relative_to(root)))
            except ValueError:
                files.append(str(path))
    files.sort()
    return ProjectInfo(root=root, files=files)


def save_index(info: ProjectInfo) -> None:
    (info.root / PROJECT_INDEX_FILE).write_text(json.dumps({"files": info.files}, indent=2), encoding="utf-8")


def load_index(root: Path) -> ProjectInfo:
    index = root / PROJECT_INDEX_FILE
    if index.exists():
        try:
            data = json.loads(index.read_text(encoding="utf-8"))
            return ProjectInfo(root=root, files=list(data.get("files", [])))
        except Exception:
            pass
    return scan_project(root)


def create_instructions(root: Path) -> Path:
    path = root / PROJECT_INSTRUCTIONS_FILE
    if not path.exists():
        path.write_text(
            "# ORBIT.md\n\n"
            "Project instructions for Orbit Code.\n\n"
            "- Be concise.\n"
            "- Explain changes before editing.\n"
            "- Prefer safe, minimal patches.\n",
            encoding="utf-8",
        )
    return path


def read_project_instructions(root: Path) -> str:
    path = root / PROJECT_INSTRUCTIONS_FILE
    if path.exists():
        return path.read_text(encoding="utf-8", errors="replace")[:8000]
    return ""


def read_file(root: Path, reference: str, max_chars: int = 12000) -> tuple[str, str]:
    clean = reference.strip().lstrip("@")
    path = (root / clean).resolve()
    if not str(path).startswith(str(root.resolve())):
        raise ValueError("File path is outside the project.")
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(clean)
    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n...[truncated]..."
    return clean, text
