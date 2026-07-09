from __future__ import annotations

from .banner import render_prompt_hint, render_startup
from .terminal import Terminal
from .tool_router import ToolRouter
from .chat import ChatSession
from .client import OpenRouterClient
from .commands import expand_file_refs, handle_command
from .config import get_api_key, load_config, save_config
from .constants import APP_DISPLAY_NAME, REQUEST_TIMEOUT
from .editor import Editor
from .models import choose_default_model
from .project import load_index, project_root, save_index
from .prompt_shell import PromptShell
from .sessions import add_recent, load_recent
from .ui import console
from .workspace import Workspace


class OrbitApp:
    """Main ORBIT application."""

    def __init__(self) -> None:
        self.config = load_config()
        self.api_key = get_api_key(self.config)

        self.client = OpenRouterClient(
            self.api_key,
            timeout=REQUEST_TIMEOUT,
        )

        self.root = project_root()

        self.workspace = Workspace(self.root)
        self.editor = Editor(self.workspace)
        self.terminal = Terminal(self.root)
        self.tool_router = ToolRouter(self.terminal)

        self.project = load_index(self.root)
        save_index(self.project)

        self._verify_api_key()

        self.model = str(self.config.get("default_model") or "")

        if not self.model:
            self.model = choose_default_model(
                self.config,
                self.client,
            ) or ""

        if not self.model:
            console.print("[red]No model selected.[/red]")
            raise SystemExit(1)

        self.chat = ChatSession(
            self.client,
            self.model,
            self.root,
        )

        self.shell = PromptShell(self.project.files)

    def run(self) -> None:
        """Run the interactive application loop."""

        render_startup(
            self.chat.model,
            self.project,
            load_recent(),
        )

        render_prompt_hint()

        add_recent(f"Opened {self.root.name or self.root}")

        while True:
            try:
                user_input = self.shell.ask()

            except (KeyboardInterrupt, EOFError):
                console.print("\n[yellow]Goodbye.[/yellow]")
                break

            if not user_input:
                continue

            if user_input.startswith("/"):
                should_continue = handle_command(
                    user_input,
                    self.chat,
                    self.config,
                    self.client,
                    self.project,
                    self.terminal,
                )

                if not should_continue:
                    break

                self.shell = PromptShell(self.project.files)
                continue
            
            tool_result = self.tool_router.handle(user_input)
            if tool_result.handled:
                continue
            
            expanded_input = expand_file_refs(
                user_input,
                self.project,
            )

            self.chat.send(expanded_input)

    def _verify_api_key(self) -> None:
        """Verify the OpenRouter API key before starting."""

        if self.client.verify_key():
            return

        console.print(
            f"[red]Invalid OpenRouter API key. "
            f"Please update your {APP_DISPLAY_NAME} config "
            "or set OPENROUTER_API_KEY.[/red]"
        )

        self.config["api_key"] = ""
        save_config(self.config)

        raise SystemExit(1)


def run_app() -> None:
    """Application entry point."""

    app = OrbitApp()
    app.run()