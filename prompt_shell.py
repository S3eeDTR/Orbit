from __future__ import annotations

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style

from .constants import CONFIG_DIR

COMMANDS = [
    "/help", "/clear", "/stats", "/model", "/models", "/index", "/files",
    "/init", "/save", "/exit", "/quit",
]


class OrbitCompleter(Completer):
    def __init__(self, project_files: list[str] | None = None) -> None:
        self.project_files = project_files or []

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        word = document.get_word_before_cursor()
        if text.startswith("/"):
            for cmd in COMMANDS:
                if cmd.startswith(word):
                    yield Completion(cmd, start_position=-len(word))
        elif "@" in text:
            token = text.split("@")[-1]
            for file in self.project_files:
                if file.startswith(token):
                    yield Completion(file, start_position=-len(token))


class PromptShell:
    def __init__(self, project_files: list[str]) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        bindings = KeyBindings()

        @bindings.add("escape", "enter")
        def _(event):
            event.current_buffer.insert_text("\n")

        self.session = PromptSession(
            history=FileHistory(str(CONFIG_DIR / "prompt_history.txt")),
            completer=OrbitCompleter(project_files),
            key_bindings=bindings,
            complete_while_typing=True,
            style=Style.from_dict({
                "prompt": "bold ansicyan",
            }),
        )

    def ask(self) -> str:
        return self.session.prompt([("class:prompt", "orbit > ")]).strip()
