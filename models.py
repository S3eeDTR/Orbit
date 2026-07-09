from __future__ import annotations

from typing import Any

from rich.prompt import Prompt
from rich.table import Table

from .client import OpenRouterClient
from .config import Config, save_config
from .ui import console


def get_cached_models(config: Config, client: OpenRouterClient, refresh: bool = False) -> list[dict[str, Any]]:
    models = [] if refresh else list(config.get("models") or [])
    if not models:
        console.print("[dim]Fetching models from OpenRouter...[/dim]")
        models = client.fetch_models()
        config["models"] = models
        save_config(config)
    return models


def filtered_models(models: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = [m for m in models if m.get("id") and not str(m.get("id")).startswith("openrouter/")]
    result.sort(key=lambda m: int(m.get("context_length") or 0), reverse=True)
    return result


def model_id_from_argument(argument: str, config: Config, client: OpenRouterClient) -> str | None:
    models = filtered_models(get_cached_models(config, client))
    argument = argument.strip()
    if not argument:
        return choose_model_interactive(config, client)
    if argument.isdigit():
        idx = int(argument) - 1
        if 0 <= idx < len(models):
            return str(models[idx]["id"])
        console.print("[red]Invalid model number.[/red]")
        return None
    return argument


def choose_model_interactive(config: Config, client: OpenRouterClient) -> str | None:
    models = filtered_models(get_cached_models(config, client))
    if not models:
        console.print("[red]No models available.[/red]")
        return None
    print_models(config, client, limit=50)
    console.print("[dim]Type a number, full model ID, or search with /claude[/dim]")
    while True:
        choice = Prompt.ask("[bold]Select model[/bold]").strip()
        if not choice:
            return None
        if choice.startswith("/"):
            term = choice[1:].lower()
            matches = [m for m in models if term in str(m.get("id", "")).lower()]
            if not matches:
                console.print("[yellow]No matches.[/yellow]")
                continue
            for i, model in enumerate(matches[:20], 1):
                console.print(f"{i:>2}. {model.get('id')}")
            continue
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(models):
                return str(models[idx]["id"])
        return choice


def choose_default_model(config: Config, client: OpenRouterClient) -> str | None:
    console.print("\n[bold cyan]Select your default model[/bold cyan]")
    model = choose_model_interactive(config, client)
    if model:
        config["default_model"] = model
        save_config(config)
        console.print(f"[green]Default model set to: {model}[/green]")
    return model


def print_models(config: Config, client: OpenRouterClient, limit: int = 40) -> None:
    models = filtered_models(get_cached_models(config, client))
    table = Table(title="Available Models", border_style="cyan")
    table.add_column("#", style="dim", width=4, justify="right")
    table.add_column("Model ID", style="cyan")
    table.add_column("Provider", style="green")
    table.add_column("Context", style="yellow", justify="right")
    table.add_column("Free", justify="center")
    table.add_column("Pricing", style="magenta")

    for idx, model in enumerate(models[:limit], 1):
        model_id = str(model.get("id", ""))
        pricing = model.get("pricing", {}) or {}
        prompt = _price(pricing.get("prompt"))
        completion = _price(pricing.get("completion"))
        price = "Free" if model_id.endswith(":free") or (prompt == 0 and completion == 0) else f"${prompt:.6f}/${completion:.6f}"
        provider = model.get("provider")
        if isinstance(provider, dict):
            provider_name = str(provider.get("name") or "Unknown")
        else:
            provider_name = str(provider or model_id.split("/")[0])
        table.add_row(
            str(idx),
            model_id,
            provider_name,
            str(model.get("context_length") or ""),
            "✅" if model_id.endswith(":free") or price == "Free" else "❌",
            price,
        )
    console.print(table)
    console.print("[dim]Use /model <number> or /model <model_id> to switch.[/dim]")


def _price(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0
