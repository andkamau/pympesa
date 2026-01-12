"""Authentication management for M-PESA API."""

from __future__ import annotations

import base64
import threading
import time
from typing import TYPE_CHECKING

import requests

from .endpoints import Environment, get_url
from .exceptions import AuthenticationError

if TYPE_CHECKING:
    pass


class TokenManager:
    """Manages OAuth2 access tokens for M-PESA API.

    Automatically fetches and refreshes tokens as needed.
    Thread-safe for concurrent access.

    Example:
        >>> token_manager = TokenManager(
        ...     consumer_key="your_key",
        ...     consumer_secret="your_secret",
        ...     env=Environment.SANDBOX
        ... )
        >>> token = token_manager.get_token()
    """

    # Refresh token 5 minutes before expiry
    EXPIRY_BUFFER_SECONDS = 300

    def __init__(
        self,
        consumer_key: str,
        consumer_secret: str,
        env: Environment | str = Environment.SANDBOX,
        timeout: int = 30,
    ) -> None:
        """Initialize the TokenManager.

        Args:
            consumer_key: M-PESA API consumer key.
            consumer_secret: M-PESA API consumer secret.
            env: API environment (sandbox or production).
            timeout: Request timeout in seconds.
        """
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.env = Environment(env) if isinstance(env, str) else env
        self.timeout = timeout

        self._token: str | None = None
        self._token_expiry: float = 0
        self._lock = threading.Lock()

    def get_token(self) -> str:
        """Get a valid access token, refreshing if necessary.

        Returns:
            A valid access token string.

        Raises:
            AuthenticationError: If token fetch fails.
        """
        with self._lock:
            if self._is_expired():
                self._fetch_token()
            return self._token  # type: ignore[return-value]

    def _is_expired(self) -> bool:
        """Check if the current token is expired or about to expire.

        Returns:
            True if token needs refresh, False otherwise.
        """
        if self._token is None:
            return True
        return time.time() >= (self._token_expiry - self.EXPIRY_BUFFER_SECONDS)

    def _fetch_token(self) -> None:
        """Fetch a new access token from the API.

        Raises:
            AuthenticationError: If the request fails.
        """
        url = get_url("oauth_token", self.env)

        # Create Basic auth credentials
        credentials = f"{self.consumer_key}:{self.consumer_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.get(url, headers=headers, timeout=self.timeout)
        except requests.RequestException as e:
            raise AuthenticationError(f"Failed to fetch token: {e}") from e

        if response.status_code != 200:
            raise AuthenticationError(
                message=f"Token request failed: {response.text}",
                status_code=response.status_code,
                response_data=self._safe_json(response),
            )

        data = response.json()

        if "access_token" not in data:
            raise AuthenticationError(
                message="Invalid token response: missing access_token",
                response_data=data,
            )

        self._token = data["access_token"]
        # Token typically expires in 3600 seconds (1 hour)
        expires_in = int(data.get("expires_in", 3600))
        self._token_expiry = time.time() + expires_in

    def _safe_json(self, response: requests.Response) -> dict:
        """Safely extract JSON from response.

        Args:
            response: The HTTP response.

        Returns:
            JSON data or empty dict if parsing fails.
        """
        try:
            return response.json()
        except ValueError:
            return {}

    def invalidate(self) -> None:
        """Invalidate the current token, forcing a refresh on next use."""
        with self._lock:
            self._token = None
            self._token_expiry = 0
