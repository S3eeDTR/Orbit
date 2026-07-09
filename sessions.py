from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime

from .constants import CONFIG_DIR, RECENT_FILE, SESSIONS_DIR


@dataclass
class RecentActivity:
    items: list[str] = field(default_factory=list)


def load_recent() -> RecentActivity:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not RECENT_FILE.exists():
        return RecentActivity()
    try:
        data = json.loads(RECENT_FILE.read_text(encoding="utf-8"))
        return RecentActivity(items=list(data.get("items", [])))
    except Exception:
        return RecentActivity()


def add_recent(item: str) -> None:
    recent = load_recent().items
    entry = f"{datetime.now().strftime('%Y-%m-%d %H:%M')}  {item}"
    recent = [entry] + [x for x in recent if item not in x]
    RECENT_FILE.write_text(json.dumps({"items": recent[:10]}, indent=2), encoding="utf-8")


def save_session(messages: list[dict], model: str) -> str:
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    name = datetime.now().strftime("session_%Y%m%d_%H%M%S.json")
    path = SESSIONS_DIR / name
    path.write_text(json.dumps({"model": model, "messages": messages}, indent=2), encoding="utf-8")
    add_recent(f"Saved {name}")
    return str(path)
