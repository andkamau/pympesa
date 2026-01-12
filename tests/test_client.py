"""Tests for pympesa Pympesa client."""

from __future__ import annotations

from typing import Any

import pytest
import responses

from pympesa import Pympesa
from pympesa.endpoints import Environment
from pympesa.exceptions import APIError, ValidationError


class TestPympesaInit:
    """Tests for Pympesa initialization."""

    def test_init_with_string_env(self, consumer_key: str, consumer_secret: str) -> None:
        """Should accept string environment."""
        client = Pympesa(
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            env="sandbox",
        )
        assert client.env == Environment.SANDBOX

    def test_init_with_enum_env(self, consumer_key: str, consumer_secret: str) -> None:
        """Should accept Environment enum."""
        client = Pympesa(
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            env=Environment.PRODUCTION,
        )
        assert client.env == Environment.PRODUCTION

    def test_default_timeout(self, consumer_key: str, consumer_secret: str) -> None:
        """Default timeout should be 30 seconds."""
        client = Pympesa(
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
        )
        assert client.timeout == 30


class TestSTKPush:
    """Tests for STK Push functionality."""

    @responses.activate
    def test_stk_push_success(
        self,
        client_with_token: Pympesa,
        mock_stk_push_response: dict[str, Any],
    ) -> None:
        """STK Push should succeed with valid parameters."""
        responses.add(
            responses.POST,
            "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
            json=mock_stk_push_response,
            status=200,
        )

        result = client_with_token.stk_push(
            shortcode="174379",
            passkey="testpasskey",
            amount=100,
            phone="254712345678",
            callback_url="https://example.com/callback",
            account_reference="Test123",
            description="Test payment",
        )

        assert result["ResponseCode"] == "0"
        assert "CheckoutRequestID" in result

    @responses.activate
    def test_stk_push_formats_phone(
        self,
        client_with_token: Pympesa,
        mock_stk_push_response: dict[str, Any],
    ) -> None:
        """STK Push should format phone number correctly."""
        responses.add(
            responses.POST,
            "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
            json=mock_stk_push_response,
            status=200,
        )

        client_with_token.stk_push(
            shortcode="174379",
            passkey="testpasskey",
            amount=100,
            phone="0712345678",  # Local format
            callback_url="https://example.com/callback",
            account_reference="Test123",
            description="Test payment",
        )

        # Check the request payload
        request_body = responses.calls[0].request.body
        assert "254712345678" in request_body.decode()

    def test_stk_push_validates_amount(self, client_with_token: Pympesa) -> None:
        """STK Push should reject invalid amount."""
        with pytest.raises(ValidationError, match="Amount must be greater than 0"):
            client_with_token.stk_push(
                shortcode="174379",
                passkey="testpasskey",
                amount=0,
                phone="254712345678",
                callback_url="https://example.com/callback",
                account_reference="Test123",
                description="Test payment",
            )

    @responses.activate
    def test_stk_push_api_error(
        self,
        client_with_token: Pympesa,
        mock_api_error_response: dict[str, Any],
    ) -> None:
        """STK Push should raise APIError on failure."""
        responses.add(
            responses.POST,
            "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
            json=mock_api_error_response,
            status=400,
        )

        with pytest.raises(APIError) as exc_info:
            client_with_token.stk_push(
                shortcode="174379",
                passkey="testpasskey",
                amount=100,
                phone="254712345678",
                callback_url="https://example.com/callback",
                account_reference="Test123",
                description="Test payment",
            )

        assert exc_info.value.status_code == 400


class TestSTKQuery:
    """Tests for STK Query functionality."""

    @responses.activate
    def test_stk_query_success(
        self,
        client_with_token: Pympesa,
        mock_stk_query_response: dict[str, Any],
    ) -> None:
        """STK Query should succeed with valid parameters."""
        responses.add(
            responses.POST,
            "https://sandbox.safaricom.co.ke/mpesa/stkpushquery/v1/query",
            json=mock_stk_query_response,
            status=200,
        )

        result = client_with_token.stk_query(
            shortcode="174379",
            passkey="testpasskey",
            checkout_request_id="ws_CO_123456789012345678",
        )

        assert result["ResponseCode"] == "0"
        assert result["ResultCode"] == "0"


class TestC2B:
    """Tests for C2B functionality."""

    @responses.activate
    def test_c2b_register_urls_success(
        self,
        client_with_token: Pympesa,
        mock_c2b_register_response: dict[str, Any],
    ) -> None:
        """C2B register URLs should succeed."""
        responses.add(
            responses.POST,
            "https://sandbox.safaricom.co.ke/mpesa/c2b/v2/registerurl",
            json=mock_c2b_register_response,
            status=200,
        )

        result = client_with_token.c2b_register_urls(
            shortcode="600000",
            confirmation_url="https://example.com/confirm",
            validation_url="https://example.com/validate",
        )

        assert result["ResponseCode"] == "0"

    @responses.activate
    def test_c2b_simulate_success(
        self,
        client_with_token: Pympesa,
    ) -> None:
        """C2B simulate should succeed in sandbox."""
        responses.add(
            responses.POST,
            "https://sandbox.safaricom.co.ke/mpesa/c2b/v2/simulate",
            json={"ResponseCode": "0", "ResponseDescription": "Accept the service request successfully."},
            status=200,
        )

        result = client_with_token.c2b_simulate(
            shortcode="600000",
            phone="254712345678",
            amount=100,
            bill_ref_number="INV001",
        )

        assert result["ResponseCode"] == "0"

    def test_c2b_simulate_rejects_production(
        self,
        consumer_key: str,
        consumer_secret: str,
        access_token: str,
    ) -> None:
        """C2B simulate should reject production environment."""
        client = Pympesa(
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            env=Environment.PRODUCTION,
        )
        client._token_manager._token = access_token
        client._token_manager._token_expiry = float("inf")

        with pytest.raises(ValidationError, match="only available in sandbox"):
            client.c2b_simulate(
                shortcode="600000",
                phone="254712345678",
                amount=100,
            )


class TestAccountBalance:
    """Tests for account balance functionality."""

    @responses.activate
    def test_account_balance_success(
        self,
        client_with_token: Pympesa,
    ) -> None:
        """Account balance query should succeed."""
        responses.add(
            responses.POST,
            "https://sandbox.safaricom.co.ke/mpesa/accountbalance/v1/query",
            json={
                "OriginatorConversationID": "12345-67890-1",
                "ConversationID": "AG_20231027_12345",
                "ResponseCode": "0",
                "ResponseDescription": "Accept the service request successfully.",
            },
            status=200,
        )

        result = client_with_token.account_balance(
            initiator_name="testapi",
            security_credential="encrypted_credential",
            shortcode="600000",
            result_url="https://example.com/result",
            timeout_url="https://example.com/timeout",
        )

        assert result["ResponseCode"] == "0"


class TestReversal:
    """Tests for reversal functionality."""

    @responses.activate
    def test_reversal_success(
        self,
        client_with_token: Pympesa,
    ) -> None:
        """Reversal should succeed."""
        responses.add(
            responses.POST,
            "https://sandbox.safaricom.co.ke/mpesa/reversal/v1/request",
            json={
                "OriginatorConversationID": "12345-67890-1",
                "ConversationID": "AG_20231027_12345",
                "ResponseCode": "0",
                "ResponseDescription": "Accept the service request successfully.",
            },
            status=200,
        )

        result = client_with_token.reversal(
            initiator_name="testapi",
            security_credential="encrypted_credential",
            shortcode="600000",
            transaction_id="OEI2AK4Q16",
            amount=100,
            result_url="https://example.com/result",
            timeout_url="https://example.com/timeout",
        )

        assert result["ResponseCode"] == "0"


class TestDynamicQR:
    """Tests for Dynamic QR functionality."""

    @responses.activate
    def test_dynamic_qr_success(
        self,
        client_with_token: Pympesa,
    ) -> None:
        """Dynamic QR should succeed."""
        responses.add(
            responses.POST,
            "https://sandbox.safaricom.co.ke/mpesa/qrcode/v1/generate",
            json={
                "ResponseCode": "00",
                "RequestID": "12345",
                "ResponseDescription": "The service request is processed successfully.",
                "QRCode": "base64encodedqrcode...",
            },
            status=200,
        )

        result = client_with_token.dynamic_qr(
            merchant_name="Test Merchant",
            ref_no="INV123",
            amount=100,
            shortcode="174379",
        )

        assert "QRCode" in result
