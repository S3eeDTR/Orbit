from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CommandResult:
    command: str
    cwd: str
    exit_code: int
    stdout: str
    stderr: str

    @property
    def success(self) -> bool:
        return self.exit_code == 0


class Terminal:
    """
    Safe terminal command runner for ORBIT.

    This class runs commands inside the workspace only.
    """

    def __init__(self, workspace: str | Path) -> None:
        self.workspace = Path(workspace).resolve()

    def run(
        self,
        command: str,
        timeout: int = 120,
    ) -> CommandResult:
        """
        Run a shell command inside the workspace.
        """

        process = subprocess.run(
            command,
            cwd=self.workspace,
            shell=True,
            text=True,
            capture_output=True,
            timeout=timeout,
        )

        return CommandResult(
            command=command,
            cwd=str(self.workspace),
            exit_code=process.returncode,
            stdout=process.stdout,
            stderr=process.stderr,
        )

    def run_safe(
        self,
        command: str,
        timeout: int = 120,
    ) -> CommandResult:
        """
        Run a command with basic dangerous-command blocking.
        """

        self._validate_command(command)

        return self.run(
            command,
            timeout=timeout,
        )

    def _validate_command(self, command: str) -> None:
        blocked = [
            "rm -rf /",
            "rm -rf *",
            "sudo",
            "mkfs",
            "dd ",
            ":(){",
            "> /dev/",
            "chmod -R 777 /",
            "chown -R",
        ]

        lowered = command.lower()

        for pattern in blocked:
            if pattern in lowered:
                raise ValueError(f"Blocked potentially dangerous command: {command}")