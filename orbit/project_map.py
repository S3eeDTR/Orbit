from __future__ import annotations

from dataclasses import dataclass

from .chat import ChatSession
from .project import ProjectInfo
from .workspace import Workspace


@dataclass
class ProjectMapEntry:
    path: str
    description: str


class ProjectMap:
    """
    Builds an AI-generated semantic map of the project.
    """

    def __init__(
        self,
        project: ProjectInfo,
        workspace: Workspace,
        chat: ChatSession,
        max_file_chars: int = 4000,
    ) -> None:
        self.project = project
        self.workspace = workspace
        self.chat = chat
        self.max_file_chars = max_file_chars

    def build(self, limit: int = 80) -> list[ProjectMapEntry]:
        entries: list[ProjectMapEntry] = []

        for path in self.project.files[:limit]:
            description = self.describe_file(path)

            entries.append(
                ProjectMapEntry(
                    path=path,
                    description=description,
                )
            )

        return entries


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

        reply = self.chat.complete_once(prompt)

        if not reply:
            return "Project source file."

        return reply.strip().replace("\n", " ")
        