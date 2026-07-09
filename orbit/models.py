from __future__ import annotations

from typing import Any

from rich.prompt import Prompt
from rich.table import Table

from .client import OpenRouterClient
from .config import Config, save_config
from .ui import console


def get_cached_models(
    config: Config,
    client: OpenRouterClient,
    refresh: bool = False,
) -> list[dict[str, Any]]:
    """Return cached models, or fetch them from OpenRouter."""

    models = [] if refresh else list(config.get("models") or [])

    if not models:
        console.print("[dim]Fetching models from OpenRouter...[/dim]")
        models = client.fetch_models()
        config["models"] = models
        save_config(config)

    return models


def filtered_models(models: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove internal OpenRouter models and sort by context length."""

    result = [
        model
        for model in models
        if model.get("id")
        and not str(model.get("id")).startswith("openrouter/")
    ]

    result.sort(
        key=lambda model: int(model.get("context_length") or 0),
        reverse=True,
    )

    return result


def model_id_from_argument(
    argument: str,
    config: Config,
    client: OpenRouterClient,
) -> str | None:
    """Resolve a model argument into a real model ID."""

    argument = argument.strip()

    if not argument:
        return choose_model_interactive(config, client)

    models = filtered_models(get_cached_models(config, client))

    if argument.isdigit():
        index = int(argument) - 1

        if 0 <= index < len(models):
            return str(models[index]["id"])

        console.print("[red]Invalid model number.[/red]")
        return None

    return argument


def choose_model_interactive(
    config: Config,
    client: OpenRouterClient,
) -> str | None:
    """Interactive model selection."""

    models = filtered_models(get_cached_models(config, client))

    if not models:
        console.print("[red]No models available.[/red]")
        return None

    visible_models = models

    while True:
        _print_model_table(visible_models, limit=50)

        console.print(
            "[dim]Type a number, full model ID, "
            "or search with /claude, /qwen, /gpt, etc.[/dim]"
        )

        choice = Prompt.ask("[bold]Select model[/bold]").strip()

        if not choice:
            return None

        if choice.startswith("/"):
            term = choice[1:].lower().strip()

            if not term:
                visible_models = models
                continue

            visible_models = [
                model
                for model in models
                if term in str(model.get("id", "")).lower()
            ]

            if not visible_models:
                console.print("[yellow]No matches found.[/yellow]")
                visible_models = models

            continue

        if choice.isdigit():
            index = int(choice) - 1

            if 0 <= index < len(visible_models):
                return str(visible_models[index]["id"])

            console.print("[red]Invalid model number.[/red]")
            continue

        return choice


def choose_default_model(
    config: Config,
    client: OpenRouterClient,
) -> str | None:
    """Choose and save the default model."""

    console.print("\n[bold cyan]Select your default model[/bold cyan]")

    model = choose_model_interactive(config, client)

    if model:
        config["default_model"] = model
        save_config(config)
        console.print(f"[green]Default model set to: {model}[/green]")

    return model


def print_models(
    config: Config,
    client: OpenRouterClient,
    limit: int = 40,
) -> None:
    """Print the available models table."""

    models = filtered_models(get_cached_models(config, client))
    _print_model_table(models, limit=limit)

    console.print(
        "[dim]Use /model <number>, /model <model_id>, "
        "or /model for interactive selection.[/dim]"
    )


def _print_model_table(
    models: list[dict[str, Any]],
    limit: int = 40,
) -> None:
    """Render a model table."""

    table = Table(title="Available Models", border_style="cyan")

    table.add_column("#", style="dim", width=4, justify="right")
    table.add_column("Model ID", style="cyan", overflow="fold")
    table.add_column("Provider", style="green")
    table.add_column("Context", style="yellow", justify="right")
    table.add_column("Free", justify="center")
    table.add_column("Pricing", style="magenta")

    for index, model in enumerate(models[:limit], 1):
        model_id = str(model.get("id", ""))

        prompt_price, completion_price = _model_prices(model)
        is_free = _is_free_model(model_id, prompt_price, completion_price)

        table.add_row(
            str(index),
            model_id,
            _provider_name(model),
            _format_context(model.get("context_length")),
            "Yes" if is_free else "No",
            "Free"
            if is_free
            else f"${prompt_price:.6f}/${completion_price:.6f}",
        )

    console.print(table)


def _provider_name(model: dict[str, Any]) -> str:
    provider = model.get("provider")

    if isinstance(provider, dict):
        return str(provider.get("name") or "Unknown")

    if provider:
        return str(provider)

    model_id = str(model.get("id", ""))

    if "/" in model_id:
        return model_id.split("/", 1)[0]

    return "Unknown"


def _model_prices(model: dict[str, Any]) -> tuple[float, float]:
    pricing = model.get("pricing", {}) or {}

    return (
        _price(pricing.get("prompt")),
        _price(pricing.get("completion")),
    )


def _is_free_model(
    model_id: str,
    prompt_price: float,
    completion_price: float,
) -> bool:
    return model_id.endswith(":free") or (
        prompt_price == 0 and completion_price == 0
    )


def _format_context(value: Any) -> str:
    try:
        context = int(value or 0)
    except (TypeError, ValueError):
        return ""

    if context >= 1_000_000:
        return f"{context // 1_000_000}M"

    if context >= 1_000:
        return f"{context // 1_000}K"

    return str(context)


def _price(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0
