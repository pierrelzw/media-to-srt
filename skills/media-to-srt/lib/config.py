"""Credential management for Douban ASR."""

import os
from pathlib import Path
from typing import Optional, Tuple


def load_credentials() -> Tuple[Optional[str], Optional[str]]:
    """Load Douban ASR credentials from environment or config file.

    Priority:
    1. Environment variables: DOUBAO_APP_ID, DOUBAO_ACCESS_TOKEN
    2. Config file: ~/.doubao-config.env

    Returns:
        Tuple of (app_id, access_token), either can be None if not found.
    """
    app_id = os.getenv("DOUBAO_APP_ID")
    token = os.getenv("DOUBAO_ACCESS_TOKEN")

    # If env vars not set, try config file
    if not app_id or not token:
        config_file = Path.home() / ".doubao-config.env"
        if config_file.exists():
            try:
                for line in config_file.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if line.startswith("DOUBAO_APP_ID="):
                        app_id = app_id or line.split("=", 1)[1].strip()
                    elif line.startswith("DOUBAO_ACCESS_TOKEN="):
                        token = token or line.split("=", 1)[1].strip()
                    elif line.startswith("DOUBAO_RESOURCE_ID="):
                        # Optional resource ID
                        pass
            except Exception as e:
                print(f"⚠️  Error reading config file: {e}")

    return app_id, token


def get_resource_id(backend: str = "flash") -> str:
    """Get Douban ASR resource ID from env or return default.

    Args:
        backend: "flash" or "standard"

    Returns:
        Resource ID string
    """
    env_id = os.getenv("DOUBAO_RESOURCE_ID")
    if env_id:
        return env_id

    # Try config file
    config_file = Path.home() / ".doubao-config.env"
    if config_file.exists():
        try:
            for line in config_file.read_text(encoding="utf-8").splitlines():
                if line.startswith("DOUBAO_RESOURCE_ID="):
                    return line.split("=", 1)[1].strip()
        except Exception:
            pass

    # Default based on backend
    defaults = {
        "flash": "volc.seedasr.auc",
        "standard": "volc.seedasr.auc",
    }
    return defaults.get(backend, defaults["flash"])


def validate_credentials(app_id: Optional[str], token: Optional[str]) -> bool:
    """Check if credentials are available."""
    return bool(app_id and token)
