from __future__ import annotations

import shlex
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ValidationCommand:
    command: str
    paths: list[str]
    description: str


class Validator:
    """
    Builds validation commands for changed files and project types.

    The Validator only selects commands. Terminal remains responsible
    for executing them safely inside the project workspace.
    """

    def __init__(self, workspace: str | Path) -> None:
        self.workspace = Path(workspace).resolve()

    def build_commands(
        self,
        paths: list[str],
    ) -> list[ValidationCommand]:
        """
        Build focused validation commands for changed files.

        Multiple commands may be returned when a task changes files
        written in different languages.
        """

        normalized_paths = list(
            dict.fromkeys(
                str(path).replace("\\", "/")
                for path in paths
            )
        )

        commands: list[ValidationCommand] = []

        python_files = self._files_with_suffix(
            normalized_paths,
            {".py"},
        )

        javascript_files = self._files_with_suffix(
            normalized_paths,
            {".js", ".cjs", ".mjs"},
        )

        typescript_files = self._files_with_suffix(
            normalized_paths,
            {".ts", ".tsx"},
        )

        c_files = self._files_with_suffix(
            normalized_paths,
            {".c"},
        )

        cpp_files = self._files_with_suffix(
            normalized_paths,
            {".cc", ".cpp", ".cxx", ".c++"},
        )

        java_files = self._files_with_suffix(
            normalized_paths,
            {".java"},
        )

        shell_files = self._files_with_suffix(
            normalized_paths,
            {".sh", ".bash"},
        )

        json_files = self._files_with_suffix(
            normalized_paths,
            {".json"},
        )

        php_files = self._files_with_suffix(
            normalized_paths,
            {".php"},
        )

        ruby_files = self._files_with_suffix(
            normalized_paths,
            {".rb"},
        )

        rust_files = self._files_with_suffix(
            normalized_paths,
            {".rs"},
        )

        go_files = self._files_with_suffix(
            normalized_paths,
            {".go"},
        )

        if python_files:
            commands.append(
                ValidationCommand(
                    command=self._command(
                        "python -m py_compile",
                        python_files,
                    ),
                    paths=python_files,
                    description="Python syntax validation",
                )
            )

        if javascript_files:
            for path in javascript_files:
                commands.append(
                    ValidationCommand(
                        command=(
                            f"node --check "
                            f"{shlex.quote(path)}"
                        ),
                        paths=[path],
                        description="JavaScript syntax validation",
                    )
                )

        if typescript_files:
            if self._exists("tsconfig.json"):
                commands.append(
                    ValidationCommand(
                        command="npx tsc --noEmit",
                        paths=typescript_files,
                        description="TypeScript project validation",
                    )
                )
            else:
                commands.append(
                    ValidationCommand(
                        command=self._command(
                            "npx tsc --noEmit",
                            typescript_files,
                        ),
                        paths=typescript_files,
                        description="TypeScript syntax validation",
                    )
                )

        if c_files:
            commands.append(
                ValidationCommand(
                    command=self._command(
                        "gcc -fsyntax-only",
                        c_files,
                    ),
                    paths=c_files,
                    description="C syntax validation",
                )
            )

        if cpp_files:
            commands.append(
                ValidationCommand(
                    command=self._command(
                        "g++ -fsyntax-only",
                        cpp_files,
                    ),
                    paths=cpp_files,
                    description="C++ syntax validation",
                )
            )

        if java_files:
            commands.append(
                ValidationCommand(
                    command=self._command(
                        "javac",
                        java_files,
                    ),
                    paths=java_files,
                    description="Java compilation validation",
                )
            )

        if shell_files:
            commands.append(
                ValidationCommand(
                    command=self._command(
                        "bash -n",
                        shell_files,
                    ),
                    paths=shell_files,
                    description="Shell syntax validation",
                )
            )

        for path in json_files:
            commands.append(
                ValidationCommand(
                    command=(
                        f"python -m json.tool "
                        f"{shlex.quote(path)}"
                    ),
                    paths=[path],
                    description="JSON syntax validation",
                )
            )

        for path in php_files:
            commands.append(
                ValidationCommand(
                    command=f"php -l {shlex.quote(path)}",
                    paths=[path],
                    description="PHP syntax validation",
                )
            )

        for path in ruby_files:
            commands.append(
                ValidationCommand(
                    command=f"ruby -c {shlex.quote(path)}",
                    paths=[path],
                    description="Ruby syntax validation",
                )
            )

        if rust_files:
            if self._exists("Cargo.toml"):
                commands.append(
                    ValidationCommand(
                        command="cargo check",
                        paths=rust_files,
                        description="Rust project validation",
                    )
                )
            else:
                for path in rust_files:
                    commands.append(
                        ValidationCommand(
                            command=(
                                f"rustc --emit metadata "
                                f"{shlex.quote(path)}"
                            ),
                            paths=[path],
                            description="Rust compilation validation",
                        )
                    )

        if go_files:
            if self._exists("go.mod"):
                commands.append(
                    ValidationCommand(
                        command="go test ./...",
                        paths=go_files,
                        description="Go project validation",
                    )
                )
            else:
                commands.append(
                    ValidationCommand(
                        command=self._command(
                            "gofmt -d",
                            go_files,
                        ),
                        paths=go_files,
                        description="Go syntax and formatting validation",
                    )
                )

        return [
            command
            for command in commands
            if self._command_available(command.command)
        ]

    def unsupported_paths(
        self,
        paths: list[str],
    ) -> list[str]:
        """
        Return changed paths that have no configured validator.
        """

        supported_suffixes = {
            ".py",
            ".js",
            ".cjs",
            ".mjs",
            ".ts",
            ".tsx",
            ".c",
            ".cc",
            ".cpp",
            ".cxx",
            ".c++",
            ".java",
            ".sh",
            ".bash",
            ".json",
            ".php",
            ".rb",
            ".rs",
            ".go",
        }

        unsupported: list[str] = []

        for path in paths:
            suffix = Path(path).suffix.lower()

            if suffix not in supported_suffixes:
                unsupported.append(path)

        return unsupported

    def _files_with_suffix(
        self,
        paths: list[str],
        suffixes: set[str],
    ) -> list[str]:
        return [
            path
            for path in paths
            if Path(path).suffix.lower() in suffixes
        ]

    def _exists(self, path: str) -> bool:
        return (self.workspace / path).exists()

    def _command(
        self,
        prefix: str,
        paths: list[str],
    ) -> str:
        quoted_paths = " ".join(
            shlex.quote(path)
            for path in paths
        )

        return f"{prefix} {quoted_paths}"

    def _command_available(
        self,
        command: str,
    ) -> bool:
        executable = command.split(maxsplit=1)[0]

        if executable == "python":
            return True

        return shutil.which(executable) is not None