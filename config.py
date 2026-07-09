from __future__ import annotations

import json
import os
from typing import Any

from rich.panel import Panel
from rich.prompt import Prompt

from .constants import (
    APP_DISPLAY_NAME,
    CONFIG_DIR,
    CONFIG_FILE,
)
from .ui import console

Config = dict[str, Any]


# ============================================================================
# DEFAULT CONFIGURATION
# ============================================================================

def default_config() -> Config:
    """Return a new default configuration."""

    return {
        "api_key": "",
        "default_model": "",
        "models": [],
    }


# ============================================================================
# LOAD / SAVE
# ============================================================================

def load_config() -> Config:
    """Load the configuration from disk."""

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    if not CONFIG_FILE.exists():
        return default_config()

    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))

    except json.JSONDecodeError:
        console.print(
            "[yellow]Configuration file is corrupted. "
            "Creating a new one...[/yellow]"
        )
        return default_config()


def save_config(config: Config) -> None:
    """Save configuration."""

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    CONFIG_FILE.write_text(
        json.dumps(config, indent=4),
        encoding="utf-8",
    )


# ============================================================================
# API KEY
# ============================================================================

def get_api_key(config: Config) -> str:
    """Return the OpenRouter API key."""

    # Environment variable has highest priority
    env_key = os.getenv("OPENROUTER_API_KEY")

    if env_key:
        return env_key

    # Stored configuration
    if config.get("api_key"):
        return str(config["api_key"])

    console.print(
        Panel.fit(
            f"[bold cyan]{APP_DISPLAY_NAME} Setup[/bold cyan]\n\n"
            "An OpenRouter API key is required.\n\n"
            "Create one at:\n"
            "[underline]https://openrouter.ai/keys[/underline]",
            border_style="cyan",
        )
    )

    api_key = Prompt.ask(
        "[bold]OpenRouter API Key[/bold]",
        password=True,
    ).strip()

    if not api_key:
        raise SystemExit("An API key is required.")

    config["api_key"] = api_key
    save_config(config)

    return api_key
