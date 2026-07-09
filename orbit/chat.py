from __future__ import annotations


from .stats import SessionStats
from pathlib import Path
import re


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

    
    def complete_once(self, prompt: str) -> str | None:
        """
        Get one non-streaming response from the model.
        Used for internal tasks like generating file edits.
        """

        if not prompt.strip():
            return None

        messages = [
            self.messages[0],
            {
                "role": "user",
                "content": prompt,
            },
        ]

        try:
            data = self.client.chat(self.model, messages)

        except OpenRouterError as exc:
            console.print(f"[red]{exc}[/red]")
            return None

        self.stats.record(data)

        choices = data.get("choices") or []

        if not choices:
            return None

        message = choices[0].get("message") or {}

        return str(message.get("content") or "").strip()


    def generate_file_edit(
            self,
            path: str,
            original_content: str,
            instruction: str,
        ) -> str | None:
        """
        Ask the model to return the full updated file content.
        """

        prompt = f"""
    You are editing a source code file.

    File path:
    {path}

    User instruction:
    {instruction}

    Current file content:

    ```text
    {original_content}
    ```

    Return ONLY the complete updated file.

    Do not explain anything.
    Do not use markdown.
    Do not wrap the response in code fences.
    """

        reply = self.complete_once(prompt)

        if not reply:
            return None

        return self._strip_code_fence(reply)

    def _strip_code_fence(self, text: str) -> str:
        """
        Remove markdown code fences if the model returns them.
        """

        match = re.match(
            r"^```(?:\w+)?\n(.*)\n```$",
            text.strip(),
            flags=re.DOTALL,
        )

        if match:
            return match.group(1)

        return text

    def show_stats(self) -> None:
        self.stats.render(self.model)


