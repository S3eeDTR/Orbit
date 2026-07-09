from __future__ import annotations

from .banner import render_prompt_hint, render_startup
from .chat import ChatSession
from .client import OpenRouterClient
from .commands import expand_file_refs, handle_command
from .config import get_api_key, load_config, save_config
from .constants import DEFAULT_MODEL
from .models import choose_default_model
from .project import load_index, project_root, save_index
from .prompt_shell import PromptShell
from .sessions import add_recent, load_recent
from .ui import console, render_markdown


class OrbitApp:
    def __init__(self) -> None:
        self.config = load_config()
        self.api_key = get_api_key(self.config)
        self.client = OpenRouterClient(self.api_key)
        self.root = project_root()
        self.project = load_index(self.root)
        save_index(self.project)

        if not self.client.verify_key():
            console.print("[red]❌ Invalid API key. Please update config or OPENROUTER_API_KEY.[/red]")
            self.config["api_key"] = ""
            save_config(self.config)
            raise SystemExit(1)

        self.model = str(self.config.get("default_model") or "")
        if not self.model:
            self.model = choose_default_model(self.config, self.client) or DEFAULT_MODEL

        self.chat = ChatSession(self.client, self.model, self.root)
        self.shell = PromptShell(self.project.files)

    def run(self) -> None:
        render_startup(self.chat.model, self.project, load_recent())
        render_prompt_hint()
        add_recent(f"Opened {self.root.name or self.root}")

        while True:
            try:
                user_input = self.shell.ask()
            except (KeyboardInterrupt, EOFError):
                console.print("\n[yellow]👋 Goodbye![/yellow]")
                break

            if not user_input:
                continue

            if user_input.startswith("/"):
                if not handle_command(user_input, self.chat, self.config, self.client, self.project):
                    break
                # refresh autocomplete after /index
                self.shell = PromptShell(self.project.files)
                continue

            expanded = expand_file_refs(user_input, self.project)
            reply = self.chat.send(expanded)
            if reply:
                render_markdown(reply)
                console.print(f"[dim]Tokens: {self.chat.total_tokens} | Cost: ${self.chat.total_cost:.6f}[/dim]\n")
