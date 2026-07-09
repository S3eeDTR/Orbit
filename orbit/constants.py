"""
Global application constants.

This module centralizes application metadata, filesystem paths,
and OpenRouter API endpoints.
"""

from pathlib import Path

# ============================================================================
# APPLICATION
# ============================================================================

APP_NAME = "orbit"
APP_DISPLAY_NAME = "ORBIT"
APP_VERSION = "0.1.0"

# ============================================================================
# FILESYSTEM
# ============================================================================

HOME_DIR = Path.home()

CONFIG_DIR = HOME_DIR / ".config" / APP_NAME

CACHE_DIR = CONFIG_DIR / "cache"
LOG_DIR = CONFIG_DIR / "logs"
SESSION_DIR = CONFIG_DIR / "sessions"

CONFIG_FILE = CONFIG_DIR / "config.json"
HISTORY_FILE = CONFIG_DIR / "history.json"
MODELS_FILE = CONFIG_DIR / "models.json"

RECENT_FILE = CONFIG_DIR / "recent.json"
SESSION_DIR = CONFIG_DIR / "sessions"

PROJECT_INSTRUCTIONS_FILE = "ORBIT.md"
PROJECT_INDEX_FILE = ".orbit_index.json"
# ============================================================================
# OPENROUTER API
# ============================================================================

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

MODELS_ENDPOINT = f"{OPENROUTER_BASE_URL}/models"
CHAT_ENDPOINT = f"{OPENROUTER_BASE_URL}/chat/completions"

# ============================================================================
# HTTP
# ============================================================================

USER_AGENT = f"{APP_NAME}/{APP_VERSION}"

HTTP_REFERER = "https://github.com/S3eeDTR/Orbit"

APPLICATION_TITLE = "ORBIT"

REQUEST_TIMEOUT = 120
MODEL_FETCH_TIMEOUT = 30
VERIFY_TIMEOUT = 10
