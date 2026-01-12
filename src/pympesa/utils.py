"""Utility functions for pympesa library."""

from __future__ import annotations

import base64
from datetime import datetime


def generate_timestamp() -> str:
    """Generate a timestamp in M-PESA's required format.

    Returns:
        Timestamp string in YYYYMMDDHHMMSS format.
    """
    return datetime.now().strftime("%Y%m%d%H%M%S")


def generate_password(shortcode: str, passkey: str, timestamp: str) -> str:
    """Generate the password for M-PESA Express (STK Push) requests.

    The password is a base64-encoded string of: shortcode + passkey + timestamp

    Args:
        shortcode: The business shortcode.
        passkey: The Lipa Na M-PESA passkey provided by Safaricom.
        timestamp: The timestamp in YYYYMMDDHHMMSS format.

    Returns:
        Base64-encoded password string.
    """
    data = f"{shortcode}{passkey}{timestamp}"
    return base64.b64encode(data.encode()).decode()


def format_phone_number(phone: str) -> str:
    """Format a phone number to the required 254XXXXXXXXX format.

    Handles common formats:
    - 0712345678 -> 254712345678
    - +254712345678 -> 254712345678
    - 254712345678 -> 254712345678
    - 712345678 -> 254712345678

    Args:
        phone: The phone number in any common format.

    Returns:
        Phone number in 254XXXXXXXXX format.

    Raises:
        ValueError: If the phone number format is invalid.
    """
    # Remove any whitespace, dashes, or parentheses
    cleaned = "".join(c for c in phone if c.isdigit() or c == "+")

    # Remove leading +
    if cleaned.startswith("+"):
        cleaned = cleaned[1:]

    # Handle different formats
    if cleaned.startswith("254"):
        result = cleaned
    elif cleaned.startswith("0"):
        result = "254" + cleaned[1:]
    elif cleaned.startswith("7") or cleaned.startswith("1"):
        result = "254" + cleaned
    else:
        raise ValueError(
            f"Invalid phone number format: {phone}. "
            "Expected format: 0712345678, +254712345678, or 254712345678"
        )

    # Validate length (should be 12 digits for Kenya)
    if len(result) != 12:
        raise ValueError(
            f"Invalid phone number length: {phone}. "
            "Expected 12 digits in format 254XXXXXXXXX"
        )

    return result
