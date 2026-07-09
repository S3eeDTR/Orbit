from __future__ import annotations

from datetime import datetime
from typing import Any

from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .client import OpenRouterClient, OpenRouterError
from .project import read_project_instructions
from .ui import console


class ChatSession:
    def __init__(self, client: OpenRouterClient, model: str, project_root=None) -> None:
        self.client = client
        self.model = model
        self.project_root = project_root
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
            "You are Orbit Code, a terminal-based developer assistant. "
            "Be practical, concise, and code-focused. When files are provided, ground your answer in them. "
            "Do not invent file contents."
        )
        if instructions:
            content += "\n\nProject instructions:\n" + instructions
        self.messages = [{"role": "system", "content": content}]

    def switch_model(self, new_model: str) -> None:
        self.model = new_model
        console.print(f"[green]✅ Switched to: {new_model}[/green]")

    def clear(self) -> None:
        self.total_tokens = 0
        self.total_cost = 0.0
        self.reset_system_prompt()
        console.print("[yellow]🗑️ Conversation history cleared.[/yellow]")

    def send(self, user_input: str) -> str | None:
        if not user_input.strip():
            return None
        self.messages.append({"role": "user", "content": user_input})
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn(f"[cyan]Thinking with {self.model}...[/cyan]"),
                transient=True,
            ):
                data = self.client.chat(self.model, self.messages)
        except OpenRouterError as exc:
            console.print(f"[red]❌ {exc}[/red]")
            self.messages.pop()
            return None

        choice = data.get("choices", [{}])[0]
        reply = choice.get("message", {}).get("content", "")
        usage = data.get("usage", {}) or {}
        self.total_tokens += int(usage.get("total_tokens") or 0)
        pricing = data.get("pricing", {}) or {}
        try:
            self.total_cost += float(pricing.get("total") or 0)
        except (TypeError, ValueError):
            pass
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
