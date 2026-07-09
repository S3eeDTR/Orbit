from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .constants import RECENT_FILE, SESSION_DIR


@dataclass
class RecentActivity:
    items: list[str] = field(default_factory=list)


def load_recent() -> RecentActivity:
    """Load recent activity."""

    RECENT_FILE.parent.mkdir(parents=True, exist_ok=True)

    if not RECENT_FILE.exists():
        return RecentActivity()

    try:
        data = json.loads(RECENT_FILE.read_text(encoding="utf-8"))
        return RecentActivity(items=list(data.get("items", [])))

    except Exception:
        return RecentActivity()


def add_recent(item: str) -> None:
    """Add one item to recent activity."""

    RECENT_FILE.parent.mkdir(parents=True, exist_ok=True)

    recent = load_recent().items

    entry = f"{datetime.now().strftime('%Y-%m-%d %H:%M')}  {item}"

    recent = [entry] + [
        existing
        for existing in recent
        if item not in existing
    ]

    RECENT_FILE.write_text(
        json.dumps(
            {
                "items": recent[:10],
            },
            indent=4,
        ),
        encoding="utf-8",
    )


def save_session(
    messages: list[dict[str, Any]],
    model: str,
) -> str:
    """Save the current chat session."""

    SESSION_DIR.mkdir(parents=True, exist_ok=True)

    name = datetime.now().strftime("session_%Y%m%d_%H%M%S.json")
    path = SESSION_DIR / name

    path.write_text(
        json.dumps(
            {
                "model": model,
                "messages": messages,
            },
            indent=4,
        ),
        encoding="utf-8",
    )

    add_recent(f"Saved {name}")

    return str(path)
