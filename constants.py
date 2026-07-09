"""
Application constants and filesystem locations.

All application paths are defined here so the project branding
and directory structure can be changed from a single location.
"""

from pathlib import Path

# ============================================================================
# APPLICATION
# ============================================================================

APP_NAME = "orbit"
APP_VERSION = "0.1.0"

# ============================================================================
# DIRECTORIES
# ============================================================================

HOME_DIR = Path.home()

CONFIG_DIR = HOME_DIR / ".config" / APP_NAME

CACHE_DIR = CONFIG_DIR / "cache"
LOG_DIR = CONFIG_DIR / "logs"
SESSION_DIR = CONFIG_DIR / "sessions"

# ============================================================================
# FILES
# ============================================================================

CONFIG_FILE = CONFIG_DIR / "config.json"
HISTORY_FILE = CONFIG_DIR / "history.json"
MODELS_FILE = CONFIG_DIR / "models.json"

# ============================================================================
# OPENROUTER
# ============================================================================

OPENROUTER_API_URL = "https://openrouter.ai/api/v1"
MODELS_ENDPOINT = f"{OPENROUTER_API_URL}/models"
CHAT_ENDPOINT = f"{OPENROUTER_API_URL}/chat/completions"

# ============================================================================
# USER AGENT
# ============================================================================

USER_AGENT = f"{APP_NAME}/{APP_VERSION}"
