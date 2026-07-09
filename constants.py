from pathlib import Path

APP_NAME = "Orbit Code"
APP_VERSION = "0.2.0"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openai/gpt-4o-mini"

CONFIG_DIR = Path.home() / ".config" / "openrouter-cli"
CONFIG_FILE = CONFIG_DIR / "config.json"
SESSIONS_DIR = CONFIG_DIR / "sessions"
RECENT_FILE = CONFIG_DIR / "recent.json"
PROJECT_INDEX_FILE = ".orbit_index.json"
PROJECT_INSTRUCTIONS_FILE = "ORBIT.md"
