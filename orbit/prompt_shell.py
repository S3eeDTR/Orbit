from __future__ import annotations

from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style

from .constants import CONFIG_DIR

COMMANDS = [
    "/help",
    "/clear",
    "/stats",
    "/model",
    "/models",
    "/index",
    "/files",
    "/init",
    "/save",
    "/exit",
    "/quit",
]


class OrbitCompleter(Completer):
    """Autocomplete slash commands and @file references."""

    def __init__(self, project_files: list[str] | None = None) -> None:
        self.project_files = project_files or []

    def get_completions(self, document: Document, complete_event):
        text = document.text_before_cursor
        word = document.get_word_before_cursor()

        if text.startswith("/"):
            for command in COMMANDS:
                if command.startswith(word):
                    yield Completion(command, start_position=-len(word))
            return

        if "@" not in text:
            return

        token = text.split("@")[-1]

        for file_path in self.project_files:
            if file_path.startswith(token):
                yield Completion(file_path, start_position=-len(token))


class PromptShell:
    """Interactive prompt shell for ORBIT."""

    def __init__(self, project_files: list[str]) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        self.history_file = CONFIG_DIR / "prompt_history.txt"

        bindings = KeyBindings()

        @bindings.add("escape", "enter")
        def _(event) -> None:
            event.current_buffer.insert_text("\n")

        self.session = PromptSession(
            history=FileHistory(str(self.history_file)),
            completer=OrbitCompleter(project_files),
            key_bindings=bindings,
            complete_while_typing=True,
            multiline=False,
            style=Style.from_dict(
                {
                    "prompt": "bold ansicyan",
                }
            ),
        )

    def ask(self) -> str:
        """Read one prompt from the user."""

        return self.session.prompt(
            [("class:prompt", "orbit ❯ ")]
        ).strip()
