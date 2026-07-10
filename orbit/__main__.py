"""
ORBIT entry point.

Allows the application to be launched using:

    python -m orbit

or, when installed:

    orbit
"""

from __future__ import annotations

import sys

from .app import run_app


def main() -> None:
    """CLI entry point."""

    arguments = sys.argv[1:]

    if not arguments:
        run_app()
        return

    command = arguments[0].lower()

    if command == "index":
        run_index_command(arguments[1:])
        return

    print(f"Unknown command: {command}")
    print_usage()
    raise SystemExit(2)


def run_index_command(arguments: list[str]) -> None:
    """Build or update ORBIT's persistent project index."""

    valid_arguments = {
        (),
        ("--refresh",),
        ("--changed",),
    }

    if tuple(arguments) not in valid_arguments:
        print("Usage: orbit index [--refresh | --changed]")
        raise SystemExit(2)

    from .chat import ChatSession
    from .client import OpenRouterClient
    from .config import get_api_key, load_config
    from .constants import REQUEST_TIMEOUT
    from .models import choose_default_model
    from .project import project_root, save_index, scan_project
    from .project_map import ProjectMap
    from .workspace import Workspace

    config = load_config()
    api_key = get_api_key(config)

    client = OpenRouterClient(
        api_key,
        timeout=REQUEST_TIMEOUT,
    )

    root = project_root()
    project = scan_project(root)
    save_index(project)

    model = str(config.get("default_model") or "")

    if not model:
        model = choose_default_model(
            config,
            client,
        ) or ""

    if not model:
        print("No model selected.")
        raise SystemExit(1)

    chat = ChatSession(
        client,
        model,
        root,
    )

    workspace = Workspace(root)

    project_map = ProjectMap(
        project,
        workspace,
        chat,
    )

    refresh = arguments == ["--refresh"]
    changed_only = arguments == ["--changed"]

    try:
        entries = project_map.index(
            refresh=refresh,
            changed_only=changed_only,
        )
    except Exception as exc:
        print(f"Project indexing failed: {exc}")
        raise SystemExit(1) from exc

    if refresh:
        print(
            f"Rebuilt persistent project index for "
            f"{len(entries)} files."
        )
    elif changed_only:
        print(
            f"Updated changed files. Persistent index contains "
            f"{len(entries)} files."
        )
    else:
        print(
            f"Updated persistent project index for "
            f"{len(entries)} files."
        )


def print_usage() -> None:
    """Print available ORBIT CLI commands."""

    print("Usage:")
    print("  orbit")
    print("  orbit index")
    print("  orbit index --refresh")
    print("  orbit index --changed")


if __name__ == "__main__":
    main()
