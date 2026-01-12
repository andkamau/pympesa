"""pympesa - Modern Python client for Safaricom M-PESA Daraja API.

Example:
    >>> from pympesa import Pympesa
    >>> client = Pympesa(
    ...     consumer_key="your_key",
    ...     consumer_secret="your_secret",
    ...     env="sandbox"
    ... )
    >>> response = client.stk_push(
    ...     shortcode="174379",
    ...     passkey="your_passkey",
    ...     amount=100,
    ...     phone="254712345678",
    ...     callback_url="https://example.com/callback",
    ...     account_reference="Order123",
    ...     description="Payment"
    ... )
"""

from .auth import TokenManager
from .client import Pympesa
from .endpoints import Environment
from .exceptions import (
    APIError,
    AuthenticationError,
    ConfigurationError,
    PympesaError,
    ValidationError,
)

__version__ = "2.0.0"

__all__ = [
    "Pympesa",
    "TokenManager",
    "Environment",
    "PympesaError",
    "AuthenticationError",
    "APIError",
    "ConfigurationError",
    "ValidationError",
    "__version__",
]
