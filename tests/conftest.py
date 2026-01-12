"""Shared pytest fixtures for pympesa tests."""

from __future__ import annotations

import json
from typing import Any, Generator
from unittest.mock import MagicMock, patch

import pytest
import responses

from pympesa import Pympesa, TokenManager
from pympesa.endpoints import Environment


# =============================================================================
# Test credentials
# =============================================================================


@pytest.fixture
def consumer_key() -> str:
    """Test consumer key."""
    return "test_consumer_key"


@pytest.fixture
def consumer_secret() -> str:
    """Test consumer secret."""
    return "test_consumer_secret"


@pytest.fixture
def access_token() -> str:
    """Test access token."""
    return "test_access_token_12345"


# =============================================================================
# Mock responses
# =============================================================================


@pytest.fixture
def mock_token_response(access_token: str) -> dict[str, Any]:
    """Mock OAuth token response."""
    return {
        "access_token": access_token,
        "expires_in": "3600",
    }


@pytest.fixture
def mock_stk_push_response() -> dict[str, Any]:
    """Mock STK Push response."""
    return {
        "MerchantRequestID": "12345-67890-1",
        "CheckoutRequestID": "ws_CO_123456789012345678",
        "ResponseCode": "0",
        "ResponseDescription": "Success. Request accepted for processing",
        "CustomerMessage": "Success. Request accepted for processing",
    }


@pytest.fixture
def mock_stk_query_response() -> dict[str, Any]:
    """Mock STK Query response."""
    return {
        "ResponseCode": "0",
        "ResponseDescription": "The service request has been accepted successfully",
        "MerchantRequestID": "12345-67890-1",
        "CheckoutRequestID": "ws_CO_123456789012345678",
        "ResultCode": "0",
        "ResultDesc": "The service request is processed successfully.",
    }


@pytest.fixture
def mock_c2b_register_response() -> dict[str, Any]:
    """Mock C2B register URL response."""
    return {
        "OriginatorCoversationID": "12345-67890-1",
        "ResponseCode": "0",
        "ResponseDescription": "Success",
    }


@pytest.fixture
def mock_api_error_response() -> dict[str, Any]:
    """Mock API error response."""
    return {
        "requestId": "12345-67890-error",
        "errorCode": "400.002.02",
        "errorMessage": "Bad Request - Invalid Amount",
    }


# =============================================================================
# TokenManager fixtures
# =============================================================================


@pytest.fixture
def token_manager(consumer_key: str, consumer_secret: str) -> TokenManager:
    """Create a TokenManager instance for testing."""
    return TokenManager(
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        env=Environment.SANDBOX,
    )


@pytest.fixture
def token_manager_with_mock(
    token_manager: TokenManager,
    mock_token_response: dict[str, Any],
) -> Generator[TokenManager, None, None]:
    """TokenManager with mocked token fetch."""
    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.GET,
            "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials",
            json=mock_token_response,
            status=200,
        )
        yield token_manager


# =============================================================================
# Pympesa client fixtures
# =============================================================================


@pytest.fixture
def client(consumer_key: str, consumer_secret: str) -> Pympesa:
    """Create a Pympesa client for testing."""
    return Pympesa(
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        env=Environment.SANDBOX,
    )


@pytest.fixture
def client_with_token(
    client: Pympesa,
    access_token: str,
) -> Pympesa:
    """Pympesa client with pre-loaded token (no network calls needed)."""
    client._token_manager._token = access_token
    client._token_manager._token_expiry = float("inf")  # Never expires
    return client


# =============================================================================
# Responses mock setup
# =============================================================================


@pytest.fixture
def mocked_responses() -> Generator[responses.RequestsMock, None, None]:
    """Activate responses mock for the duration of a test."""
    with responses.RequestsMock() as rsps:
        yield rsps
