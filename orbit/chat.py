from __future__ import annotations


from .stats import SessionStats
from pathlib import Path


from .ui import stream_text, finish_stream
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
        self.stats = SessionStats()
        

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
        self.stats.reset()
        self.reset_system_prompt()
        console.print("[yellow]Conversation history cleared.[/yellow]")

    def send(self, user_input: str) -> str | None:
        return self.send_stream(user_input)
    

    def send_stream(self, user_input: str) -> str | None:
        if not user_input.strip():
            return None

        self.messages.append(
            {
                "role": "user", 
                "content": user_input,
             }
             
             )

        console.print(f"[dim]Thinking with {self.model}...[/dim]\n")

        chunks: list[str] = []

        try:
            for chunk in self.client.chat_stream(self.model, self.messages):
                chunks.append(chunk)
                stream_text(chunk)

            finish_stream()

        except OpenRouterError as exc:
            console.print(f"\n[red]{exc}[/red]")

            if self.messages and self.messages[-1]["role"] == "user":
                self.messages.pop()

            return None

        reply = "".join(chunks).strip()

        if not reply:
            console.print("[yellow]Model returned an empty response.[/yellow]")
            return None

        self.messages.append(
            {
                "role": "assistant", 
                "content": reply,
            }
        )   
        return reply

    def show_stats(self) -> None:
        self.stats.render(self.model)


