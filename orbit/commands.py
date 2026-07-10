
from __future__ import annotations

import re

from rich.panel import Panel
from rich.table import Table

from .chat import ChatSession
from .checkpoints import CheckpointManager
from .client import OpenRouterClient
from .config import Config, save_config
from .editor import Editor
from .models import model_id_from_argument, print_models
from .project import (
    ProjectInfo,
    create_instructions,
    read_file,
    save_index,
    scan_project,
)
from .project_map import ProjectMap
from .sessions import save_session
from .terminal import Terminal
from .ui import console, ok, warn
from .workspace import Workspace


HELP_TEXT = """
[bold cyan]Commands[/bold cyan]
  /help               Show this help menu
  /clear              Clear conversation history
  /model              Interactive model picker
  /model <number>     Switch using number from /models
  /model <id>         Switch using exact OpenRouter model ID
  /models             List available models
  /run <command>      Run terminal commands
  /index              Update new and changed project files
  /index --refresh    Rebuild the complete project index
  /index --changed    Re-index only new and changed files
  /files              Show indexed files
  /init               Create ORBIT.md project instructions
  /save               Save current chat session
  /stats              Show session statistics
  /history            Show recent edit checkpoints
  /show checkpoint ID Show checkpoint details
  /undo [ID]          Undo the latest or selected checkpoint
  /exit               Exit

[bold cyan]Project usage[/bold cyan]
  explain @main.py
  fix the bug in @orbit/client.py
  summarize @README.md and @pyproject.toml
"""

FILE_REF_RE = re.compile(r"@([A-Za-z0-9_./\\-]+)")


def expand_file_refs(text: str, project: ProjectInfo) -> str:
    """Expand @file references into attached file content."""

    refs = FILE_REF_RE.findall(text)

    if not refs:
        return text

    parts = [
        text,
        "\n\n--- Attached files ---",
    ]

    for ref in refs:
        try:
            name, content = read_file(project.root, ref)
            parts.append(
                f"\n\nFile: {name}\n"
                "```text\n"
                f"{content}\n"
                "```"
            )

        except Exception as exc:
            parts.append(f"\n\nCould not read @{ref}: {exc}")

    return "".join(parts)


def handle_command(
    command_line: str,
    chat: ChatSession,
    config: Config,
    client: OpenRouterClient,
    project: ProjectInfo,
    terminal: Terminal,
    checkpoints: CheckpointManager,
) -> bool:
    """Handle slash commands. Return False when the app should exit."""

    parts = command_line.split(maxsplit=1)

    command = parts[0].lower()
    argument = parts[1].strip() if len(parts) > 1 else ""

    if command in {"/exit", "/quit"}:
        console.print("[yellow]Goodbye.[/yellow]")
        return False

    if command == "/help":
        console.print(
            Panel(
                HELP_TEXT,
                title="Help",
                border_style="cyan",
            )
        )

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
        valid_arguments = {"", "--refresh", "--changed"}

        if argument not in valid_arguments:
            warn("Usage: /index [--refresh | --changed]")
            return True

        # Refresh the basic project file list first so new and deleted files
        # are reflected before updating the semantic project map.
        new_info = scan_project(project.root)
        project.files[:] = new_info.files
        save_index(project)

        try:
            workspace = Workspace(project.root)

            project_map = ProjectMap(
                project=project,
                workspace=workspace,
                chat=chat,
            )

            entries = project_map.index(
                refresh=argument == "--refresh",
                changed_only=argument == "--changed",
            )

        except Exception as exc:
            warn(f"Project indexing failed: {exc}")
            return True

        if argument == "--refresh":
            ok(f"Rebuilt project index for {len(entries)} files.")
        elif argument == "--changed":
            ok(f"Updated changed project files. Index contains {len(entries)} files.")
        else:
            ok(f"Updated project index for {len(entries)} files.")

    elif command == "/files":
        table = Table(
            title=f"Indexed files ({project.file_count})",
            border_style="cyan",
        )

        table.add_column("#", justify="right", style="dim")
        table.add_column("Path", style="cyan")

        for index, path in enumerate(project.files[:100], 1):
            table.add_row(str(index), path)

        console.print(table)

        if project.file_count > 100:
            console.print(
                f"[dim]Showing first 100 of {project.file_count} files.[/dim]"
            )

    elif command == "/run":
        if not argument:
            warn("Usage: /run <command>")
            return True

        try:
            result = terminal.run_safe(argument)
        except Exception as exc:
            warn(str(exc))
            return True

        console.print(f"[bold cyan]Command:[/bold cyan] {result.command}")
        console.print(f"[bold cyan]Exit code:[/bold cyan] {result.exit_code}")

        if result.stdout:
            console.print(
                Panel(
                    result.stdout,
                    title="stdout",
                    border_style="green",
                )
            )

        if result.stderr:
            console.print(
                Panel(
                    result.stderr,
                    title="stderr",
                    border_style="red",
                )
            )


    elif command == "/history":
        items = checkpoints.list()

        if not items:
            warn("No checkpoints found.")
            return True

        table = Table(title="Edit checkpoints", border_style="cyan")
        table.add_column("ID", style="cyan")
        table.add_column("Created", style="dim")
        table.add_column("Files", justify="right")
        table.add_column("Status")
        table.add_column("Instruction")

        for item in items:
            table.add_row(
                item.id,
                item.created_at.replace("T", " ")[:19],
                str(len(item.files)),
                "undone" if item.undone else "active",
                item.instruction or "-",
            )

        console.print(table)

    elif command == "/show":
        show_parts = argument.split(maxsplit=1)

        if len(show_parts) != 2 or show_parts[0].lower() != "checkpoint":
            warn("Usage: /show checkpoint <id>")
            return True

        try:
            checkpoint = checkpoints.get(show_parts[1])
        except ValueError as exc:
            warn(str(exc))
            return True

        table = Table(
            title=f"Checkpoint {checkpoint.id}",
            border_style="cyan",
        )
        table.add_column("Property", style="cyan")
        table.add_column("Value")
        table.add_row("Created", checkpoint.created_at)
        table.add_row("Status", "undone" if checkpoint.undone else "active")
        table.add_row("Instruction", checkpoint.instruction or "-")
        table.add_row("Files", "\n".join(item.path for item in checkpoint.files))
        console.print(table)

    elif command == "/undo":
        checkpoint_id = argument or None

        try:
            checkpoint = checkpoints.undo(
                Editor(Workspace(project.root)),
                checkpoint_id,
            )
        except Exception as exc:
            warn(f"Undo failed: {exc}")
            return True

        ok(
            f"Undid checkpoint {checkpoint.id} and restored "
            f"{len(checkpoint.files)} file(s)."
        )

    elif command == "/init":
        path = create_instructions(project.root)
        chat.reset_system_prompt()
        ok(f"Created or loaded {path.name}")

    elif command == "/save":
        path = save_session(chat.messages, chat.model)
        ok(f"Saved session: {path}")

    else:
        warn(f"Unknown command: {command}. Type /help.")

    return True
