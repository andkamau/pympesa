"""M-PESA API endpoint definitions."""

from __future__ import annotations

from enum import Enum


class Environment(str, Enum):
    """M-PESA API environments."""

    SANDBOX = "sandbox"
    PRODUCTION = "production"


# Base URLs for each environment
BASE_URLS: dict[Environment, str] = {
    Environment.SANDBOX: "https://sandbox.safaricom.co.ke",
    Environment.PRODUCTION: "https://api.safaricom.co.ke",
}

# API endpoint paths
ENDPOINTS = {
    # Authentication
    "oauth_token": "/oauth/v1/generate?grant_type=client_credentials",
    # M-PESA Express (STK Push)
    "stk_push": "/mpesa/stkpush/v1/processrequest",
    "stk_query": "/mpesa/stkpushquery/v1/query",
    # Customer to Business (C2B)
    "c2b_register": "/mpesa/c2b/v2/registerurl",
    "c2b_simulate": "/mpesa/c2b/v2/simulate",
    # Business to Customer (B2C)
    "b2c_payment": "/mpesa/b2c/v1/paymentrequest",
    # Business to Business (B2B)
    "b2b_payment": "/mpesa/b2b/v1/paymentrequest",
    # Transaction Status
    "transaction_status": "/mpesa/transactionstatus/v1/query",
    # Account Balance
    "account_balance": "/mpesa/accountbalance/v1/query",
    # Reversal
    "reversal": "/mpesa/reversal/v1/request",
    # Tax Remittance
    "tax_remittance": "/mpesa/b2b/v1/remittax",
    # Dynamic QR
    "dynamic_qr": "/mpesa/qrcode/v1/generate",
}


def get_url(endpoint: str, env: Environment = Environment.SANDBOX) -> str:
    """Get the full URL for an endpoint.

    Args:
        endpoint: The endpoint key from ENDPOINTS dict.
        env: The environment (sandbox or production).

    Returns:
        The full URL for the endpoint.

    Raises:
        ValueError: If the endpoint is not found.
    """
    if endpoint not in ENDPOINTS:
        raise ValueError(f"Unknown endpoint: {endpoint}")

    base_url = BASE_URLS[env]
    return f"{base_url}{ENDPOINTS[endpoint]}"
