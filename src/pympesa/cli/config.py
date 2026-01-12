"""Configuration management for pympesa CLI."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


class Config:
    """Manages CLI configuration stored in ~/.pympesa/config.json.

    Configuration values are stored in JSON format. Credentials (consumer_key,
    consumer_secret) are read from environment variables only for security.

    Environment variables:
        MPESA_CONSUMER_KEY: M-PESA API consumer key
        MPESA_CONSUMER_SECRET: M-PESA API consumer secret
    """

    DEFAULT_CONFIG_DIR = Path.home() / ".pympesa"
    DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.json"

    # Keys that can be stored in config file
    ALLOWED_KEYS = {
        "environment",
        "shortcode",
        "passkey",
        "initiator_name",
        "callback_url",
        "result_url",
        "timeout_url",
        "validation_url",
        "confirmation_url",
    }

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize configuration manager.

        Args:
            config_path: Optional custom path to config file.
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_FILE
        self._data: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        """Load configuration from file."""
        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, OSError):
                self._data = {}
        else:
            self._data = {}

    def save(self) -> None:
        """Save configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w") as f:
            json.dump(self._data, f, indent=2)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key.
            default: Default value if key not found.

        Returns:
            Configuration value or default.
        """
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value.

        Args:
            key: Configuration key.
            value: Value to set.

        Raises:
            ValueError: If key is not allowed in config file.
        """
        if key not in self.ALLOWED_KEYS:
            raise ValueError(
                f"Key '{key}' cannot be stored in config file. "
                f"Allowed keys: {', '.join(sorted(self.ALLOWED_KEYS))}"
            )
        self._data[key] = value

    def delete(self, key: str) -> None:
        """Delete a configuration value.

        Args:
            key: Configuration key to delete.
        """
        self._data.pop(key, None)

    def clear(self) -> None:
        """Clear all configuration."""
        self._data = {}

    @property
    def consumer_key(self) -> str | None:
        """Get consumer key from environment variable."""
        return os.environ.get("MPESA_CONSUMER_KEY")

    @property
    def consumer_secret(self) -> str | None:
        """Get consumer secret from environment variable."""
        return os.environ.get("MPESA_CONSUMER_SECRET")

    @property
    def has_credentials(self) -> bool:
        """Check if credentials are available in environment."""
        return bool(self.consumer_key and self.consumer_secret)

    @property
    def environment(self) -> str:
        """Get the configured environment (sandbox/production)."""
        return self.get("environment", "sandbox")

    def to_dict(self) -> dict[str, Any]:
        """Get all configuration as a dictionary.

        Returns:
            Dictionary of configuration values (excludes credentials).
        """
        return dict(self._data)

    def __repr__(self) -> str:
        return f"Config(path={self.config_path}, keys={list(self._data.keys())})"
