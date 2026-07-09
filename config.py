import json
import os
from typing import Any

from rich.panel import Panel
from rich.prompt import Prompt

from .constants import CONFIG_DIR, CONFIG_FILE
from .ui import console

Config = dict[str, Any]


def default_config() -> Config:
    return {"api_key": "", "default_model": "", "models": []}


def load_config() -> Config:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        return default_config()

    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        console.print("[yellow]⚠️ Config file is invalid. Creating a clean config.[/yellow]")
        return default_config()


def save_config(config: Config) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2), encoding="utf-8")


def get_api_key(config: Config) -> str:
    env_key = os.getenv("OPENROUTER_API_KEY")
    if env_key:
        return env_key

    if config.get("api_key"):
        return str(config["api_key"])

    console.print(Panel.fit(
        "[bold cyan]🔑 OpenRouter API Key Required[/bold cyan]\n"
        "Get your key at: [underline]https://openrouter.ai/keys[/underline]",
        border_style="cyan",
    ))
    api_key = Prompt.ask("[bold]Enter your OpenRouter API key[/bold]", password=True).strip()
    if not api_key:
        raise SystemExit("API key is required.")

    config["api_key"] = api_key
    save_config(config)
    return api_key
