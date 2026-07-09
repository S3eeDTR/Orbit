from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from rich.table import Table

from .ui import console


@dataclass
class SessionStats:
    """
    Tracks statistics for the current ORBIT session.
    """

    session_start: datetime = field(default_factory=datetime.now)

    requests: int = 0

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    total_cost: float = 0.0

    last_prompt_tokens: int = 0
    last_completion_tokens: int = 0
    last_total_tokens: int = 0
    last_cost: float = 0.0

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------

    def record(self, response: dict[str, Any]) -> None:
        """
        Record usage statistics from an OpenRouter response.
        """

        self.requests += 1

        usage = response.get("usage", {}) or {}

        prompt = int(usage.get("prompt_tokens") or 0)
        completion = int(usage.get("completion_tokens") or 0)
        total = int(usage.get("total_tokens") or 0)

        pricing = response.get("pricing", {}) or {}

        try:
            cost = float(pricing.get("total") or 0)
        except (TypeError, ValueError):
            cost = 0.0

        # Last request

        self.last_prompt_tokens = prompt
        self.last_completion_tokens = completion
        self.last_total_tokens = total
        self.last_cost = cost

        # Session totals

        self.prompt_tokens += prompt
        self.completion_tokens += completion
        self.total_tokens += total
        self.total_cost += cost

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @property
    def duration(self) -> str:
        return str(datetime.now() - self.session_start).split(".")[0]

    @property
    def average_tokens(self) -> int:
        if self.requests == 0:
            return 0

        return self.total_tokens // self.requests

    @property
    def average_cost(self) -> float:
        if self.requests == 0:
            return 0.0

        return self.total_cost / self.requests

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render(self, model: str) -> None:

        table = Table(
            title="Session Statistics",
            border_style="cyan",
        )

        table.add_column("Metric", style="bold")
        table.add_column("Value", style="green")

        table.add_row("Model", model)

        table.add_row("Requests", str(self.requests))

        table.add_row("Prompt Tokens", f"{self.prompt_tokens:,}")
        table.add_row("Completion Tokens", f"{self.completion_tokens:,}")
        table.add_row("Total Tokens", f"{self.total_tokens:,}")

        table.add_row("Average Tokens", f"{self.average_tokens:,}")

        table.add_row("Average Cost", f"${self.average_cost:.6f}")

        table.add_row("Total Cost", f"${self.total_cost:.6f}")

        table.add_row("Duration", self.duration)

        console.print(table)

    # ------------------------------------------------------------------
    # Footer
    # ------------------------------------------------------------------

    def render_footer(self) -> None:
        """
        Print a small footer after each completed request.
        """

        console.print(
            f"[dim]"
            f"Request #{self.requests} | "
            f"Last: {self.last_total_tokens:,} tokens | "
            f"Session: {self.total_tokens:,} tokens | "
            f"Cost: ${self.total_cost:.6f}"
            f"[/dim]"
        )

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def reset(self) -> None:

        self.session_start = datetime.now()

        self.requests = 0

        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_tokens = 0

        self.total_cost = 0.0

        self.last_prompt_tokens = 0
        self.last_completion_tokens = 0
        self.last_total_tokens = 0

        self.last_cost = 0.0
