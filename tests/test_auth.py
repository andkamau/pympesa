"""Tests for pympesa authentication module."""

from __future__ import annotations

import time
from typing import Any
from unittest.mock import patch

import pytest
import responses

from pympesa.auth import TokenManager
from pympesa.endpoints import Environment
from pympesa.exceptions import AuthenticationError


class TestTokenManager:
    """Tests for TokenManager class."""

    def test_init_with_string_env(self, consumer_key: str, consumer_secret: str) -> None:
        """Should accept string environment."""
        manager = TokenManager(
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            env="sandbox",
        )
        assert manager.env == Environment.SANDBOX

    def test_init_with_enum_env(self, consumer_key: str, consumer_secret: str) -> None:
        """Should accept Environment enum."""
        manager = TokenManager(
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            env=Environment.PRODUCTION,
        )
        assert manager.env == Environment.PRODUCTION

    def test_token_not_fetched_on_init(self, token_manager: TokenManager) -> None:
        """Token should not be fetched during initialization."""
        assert token_manager._token is None
        assert token_manager._token_expiry == 0

    @responses.activate
    def test_get_token_fetches_on_first_call(
        self,
        token_manager: TokenManager,
        mock_token_response: dict[str, Any],
        access_token: str,
    ) -> None:
        """First call to get_token should fetch from API."""
        responses.add(
            responses.GET,
            "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials",
            json=mock_token_response,
            status=200,
        )

        token = token_manager.get_token()

        assert token == access_token
        assert len(responses.calls) == 1

    @responses.activate
    def test_get_token_caches_token(
        self,
        token_manager: TokenManager,
        mock_token_response: dict[str, Any],
    ) -> None:
        """Subsequent calls should use cached token."""
        responses.add(
            responses.GET,
            "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials",
            json=mock_token_response,
            status=200,
        )

        # Call twice
        token_manager.get_token()
        token_manager.get_token()

        # Should only make one API call
        assert len(responses.calls) == 1

    @responses.activate
    def test_get_token_refreshes_when_expired(
        self,
        token_manager: TokenManager,
        mock_token_response: dict[str, Any],
    ) -> None:
        """Token should be refreshed when expired."""
        responses.add(
            responses.GET,
            "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials",
            json=mock_token_response,
            status=200,
        )

        # Get initial token
        token_manager.get_token()

        # Expire the token
        token_manager._token_expiry = time.time() - 100

        # Get token again - should refresh
        token_manager.get_token()

        assert len(responses.calls) == 2

    @responses.activate
    def test_get_token_refreshes_within_buffer(
        self,
        token_manager: TokenManager,
        mock_token_response: dict[str, Any],
    ) -> None:
        """Token should be refreshed when within expiry buffer."""
        responses.add(
            responses.GET,
            "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials",
            json=mock_token_response,
            status=200,
        )

        # Get initial token
        token_manager.get_token()

        # Set expiry to be within buffer (less than 5 minutes from now)
        token_manager._token_expiry = time.time() + 60  # 1 minute

        # Get token again - should refresh
        token_manager.get_token()

        assert len(responses.calls) == 2

    @responses.activate
    def test_authentication_error_on_failure(
        self,
        token_manager: TokenManager,
    ) -> None:
        """Should raise AuthenticationError on failed request."""
        responses.add(
            responses.GET,
            "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials",
            json={"error": "invalid_client"},
            status=401,
        )

        with pytest.raises(AuthenticationError) as exc_info:
            token_manager.get_token()

        assert exc_info.value.status_code == 401

    @responses.activate
    def test_authentication_error_missing_token(
        self,
        token_manager: TokenManager,
    ) -> None:
        """Should raise AuthenticationError if response missing access_token."""
        responses.add(
            responses.GET,
            "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials",
            json={"something": "else"},
            status=200,
        )

        with pytest.raises(AuthenticationError, match="missing access_token"):
            token_manager.get_token()

    def test_invalidate_clears_token(
        self,
        token_manager: TokenManager,
        access_token: str,
    ) -> None:
        """Invalidate should clear the cached token."""
        # Manually set a token
        token_manager._token = access_token
        token_manager._token_expiry = time.time() + 3600

        # Invalidate
        token_manager.invalidate()

        assert token_manager._token is None
        assert token_manager._token_expiry == 0
