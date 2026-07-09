from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from rich.table import Table

from .client import OpenRouterClient, OpenRouterError
from .project import read_project_instructions
from .ui import console


class ChatSession:
    """Manage one interactive chat session."""

    def __init__(
        self,
        client: OpenRouterClient,
        model: str,
        project_root: str | Path | None = None,
    ) -> None:
        self.client = client
        self.model = model
        self.project_root = Path(project_root) if project_root else None

        self.messages: list[dict[str, str]] = []
        self.total_tokens = 0
        self.total_cost = 0.0
        self.session_start = datetime.now()

        self.reset_system_prompt()

    def reset_system_prompt(self) -> None:
        instructions = ""

        if self.project_root:
            instructions = read_project_instructions(self.project_root)

        content = (
            "You are ORBIT, a terminal-based AI coding assistant. "
            "You help developers understand, refactor, debug, and improve software projects. "
            "Be practical, concise, and code-focused. "
            "When file contents are provided, ground your answer in those files. "
            "Do not invent file contents, paths, dependencies, or behavior."
        )

        if instructions:
            content += "\n\nProject instructions:\n" + instructions

        self.messages = [{"role": "system", "content": content}]

    def switch_model(self, new_model: str) -> None:
        self.model = new_model
        console.print(f"[green]Switched to: {new_model}[/green]")

    def clear(self) -> None:
        self.total_tokens = 0
        self.total_cost = 0.0
        self.session_start = datetime.now()
        self.reset_system_prompt()
        console.print("[yellow]Conversation history cleared.[/yellow]")

    def send(self, user_input: str, stream: bool = True) -> str | None:
        if stream:
            return self.send_stream(user_input)

        return self.send_once(user_input)

    def send_stream(self, user_input: str) -> str | None:
        if not user_input.strip():
            return None

        self.messages.append({"role": "user", "content": user_input})

        console.print(f"[dim]Thinking with {self.model}...[/dim]\n")

        chunks: list[str] = []

        try:
            for chunk in self.client.chat_stream(self.model, self.messages):
                chunks.append(chunk)
                console.print(chunk, end="")

            console.print()

        except OpenRouterError as exc:
            console.print(f"\n[red]{exc}[/red]")

            if self.messages and self.messages[-1]["role"] == "user":
                self.messages.pop()

            return None

        reply = "".join(chunks).strip()

        if not reply:
            console.print("[yellow]Model returned an empty response.[/yellow]")
            return None

        self.messages.append({"role": "assistant", "content": reply})

        # Streaming responses often do not return usage.
        # Keep an approximate message count, but token/cost may remain zero.
        return reply

    def send_once(self, user_input: str) -> str | None:
        if not user_input.strip():
            return None

        self.messages.append({"role": "user", "content": user_input})

        try:
            data = self.client.chat(self.model, self.messages)

        except OpenRouterError as exc:
            console.print(f"[red]{exc}[/red]")

            if self.messages and self.messages[-1]["role"] == "user":
                self.messages.pop()

            return None

        reply = self._extract_reply(data)

        if not reply:
            console.print("[yellow]Model returned an empty response.[/yellow]")
            return None

        self._track_usage(data)
        self.messages.append({"role": "assistant", "content": reply})

        return reply

    def show_stats(self) -> None:
        duration = datetime.now() - self.session_start

        table = Table(title="Session Statistics", border_style="cyan")
        table.add_column("Metric", style="bold")
        table.add_column("Value", style="green")

        table.add_row("Model", self.model)
        table.add_row("Messages", str(max(0, len(self.messages) - 1)))
        table.add_row("Total Tokens", str(self.total_tokens))
        table.add_row("Total Cost", f"${self.total_cost:.6f}")
        table.add_row("Duration", str(duration).split(".")[0])

        console.print(table)

    def _extract_reply(self, data: dict[str, Any]) -> str:
        choices = data.get("choices") or []

        if not choices:
            return ""

        message = choices[0].get("message") or {}

        return str(message.get("content") or "")

    def _track_usage(self, data: dict[str, Any]) -> None:
        usage = data.get("usage", {}) or {}

        try:
            self.total_tokens += int(usage.get("total_tokens") or 0)
        except (TypeError, ValueError):
            pass

        pricing = data.get("pricing", {}) or {}

        try:
            self.total_cost += float(pricing.get("total") or 0)
        except (TypeError, ValueError):
            pass
