from __future__ import annotations

import re

from rich.panel import Panel
from rich.table import Table

from .chat import ChatSession
from .client import OpenRouterClient
from .config import Config, save_config
from .models import model_id_from_argument, print_models
from .project import ProjectInfo, create_instructions, read_file, save_index, scan_project
from .sessions import save_session
from .ui import console, ok, render_markdown, warn

HELP_TEXT = """
[bold cyan]Commands[/bold cyan]
  /help             Show this help menu
  /clear            Clear conversation history
  /model            Interactive model picker
  /model <number>   Switch using number from /models
  /model <id>       Switch using exact OpenRouter model ID
  /models           List available models
  /index            Scan project files
  /files            Show indexed files
  /init             Create ORBIT.md project instructions
  /save             Save current chat session
  /stats            Show session statistics
  /exit             Exit

[bold cyan]Project usage[/bold cyan]
  explain @main.py
  fix the bug in @openrouter_cli/client.py
  summarize @README.md and @pyproject.toml
"""

FILE_REF_RE = re.compile(r"@([A-Za-z0-9_./\\-]+)")


def expand_file_refs(text: str, project: ProjectInfo) -> str:
    refs = FILE_REF_RE.findall(text)
    if not refs:
        return text
    parts = [text, "\n\n--- Attached files ---"]
    for ref in refs:
        try:
            name, content = read_file(project.root, ref)
            parts.append(f"\n\nFile: {name}\n```\n{content}\n```")
        except Exception as exc:
            parts.append(f"\n\nCould not read @{ref}: {exc}")
    return "".join(parts)


def handle_command(command_line: str, chat: ChatSession, config: Config, client: OpenRouterClient, project: ProjectInfo) -> bool:
    parts = command_line.split(maxsplit=1)
    command = parts[0].lower()
    argument = parts[1].strip() if len(parts) > 1 else ""

    if command in {"/exit", "/quit"}:
        console.print("[yellow]👋 Goodbye![/yellow]")
        return False
    if command == "/help":
        console.print(Panel(HELP_TEXT, title="📖 Help", border_style="cyan"))
    elif command == "/clear":
        chat.clear()
    elif command == "/stats":
        chat.show_stats()
    elif command == "/model":
        model = model_id_from_argument(argument, config, client)
        if model:
            chat.switch_model(model)
            config["default_model"] = model
            save_config(config)
    elif command == "/models":
        print_models(config, client)
    elif command == "/index":
        new_info = scan_project(project.root)
        project.files[:] = new_info.files
        save_index(project)
        ok(f"Indexed {project.file_count} files.")
    elif command == "/files":
        table = Table(title=f"Indexed files ({project.file_count})", border_style="cyan")
        table.add_column("#", justify="right", style="dim")
        table.add_column("Path", style="cyan")
        for idx, path in enumerate(project.files[:100], 1):
            table.add_row(str(idx), path)
        console.print(table)
        if project.file_count > 100:
            console.print(f"[dim]Showing first 100 of {project.file_count} files.[/dim]")
    elif command == "/init":
        path = create_instructions(project.root)
        chat.reset_system_prompt()
        ok(f"Created/loaded {path.name}")
    elif command == "/save":
        path = save_session(chat.messages, chat.model)
        ok(f"Saved session: {path}")
    else:
        warn(f"Unknown command: {command}. Type /help.")
    return True
