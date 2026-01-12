"""Tests for pympesa utility functions."""

from __future__ import annotations

import base64
import re
from datetime import datetime

import pytest

from pympesa.utils import format_phone_number, generate_password, generate_timestamp


class TestGenerateTimestamp:
    """Tests for generate_timestamp function."""

    def test_returns_string(self) -> None:
        """Timestamp should be a string."""
        result = generate_timestamp()
        assert isinstance(result, str)

    def test_format_is_correct(self) -> None:
        """Timestamp should match YYYYMMDDHHMMSS format."""
        result = generate_timestamp()
        assert len(result) == 14
        assert result.isdigit()

    def test_timestamp_is_current(self) -> None:
        """Timestamp should be close to current time."""
        result = generate_timestamp()
        now = datetime.now()

        # Extract parts from result
        year = int(result[0:4])
        month = int(result[4:6])
        day = int(result[6:8])

        assert year == now.year
        assert month == now.month
        assert day == now.day


class TestGeneratePassword:
    """Tests for generate_password function."""

    def test_returns_base64_string(self) -> None:
        """Password should be a valid base64 string."""
        result = generate_password("174379", "passkey123", "20231027120000")

        # Should be decodable
        decoded = base64.b64decode(result)
        assert decoded is not None

    def test_correct_encoding(self) -> None:
        """Password should be correctly encoded."""
        shortcode = "174379"
        passkey = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"
        timestamp = "20231027120000"

        result = generate_password(shortcode, passkey, timestamp)

        # Verify by decoding
        expected = f"{shortcode}{passkey}{timestamp}"
        expected_encoded = base64.b64encode(expected.encode()).decode()

        assert result == expected_encoded

    def test_different_inputs_produce_different_outputs(self) -> None:
        """Different inputs should produce different passwords."""
        password1 = generate_password("174379", "key1", "20231027120000")
        password2 = generate_password("174379", "key2", "20231027120000")
        password3 = generate_password("174380", "key1", "20231027120000")

        assert password1 != password2
        assert password1 != password3


class TestFormatPhoneNumber:
    """Tests for format_phone_number function."""

    def test_already_formatted(self) -> None:
        """Number already in 254 format should stay the same."""
        assert format_phone_number("254712345678") == "254712345678"

    def test_with_plus(self) -> None:
        """Number with + prefix should be formatted."""
        assert format_phone_number("+254712345678") == "254712345678"

    def test_with_leading_zero(self) -> None:
        """Number with 0 prefix should be formatted."""
        assert format_phone_number("0712345678") == "254712345678"

    def test_without_prefix(self) -> None:
        """Number starting with 7 should be formatted."""
        assert format_phone_number("712345678") == "254712345678"

    def test_with_spaces(self) -> None:
        """Number with spaces should be formatted."""
        assert format_phone_number("0712 345 678") == "254712345678"

    def test_with_dashes(self) -> None:
        """Number with dashes should be formatted."""
        assert format_phone_number("0712-345-678") == "254712345678"

    def test_starting_with_1(self) -> None:
        """Number starting with 1 (Safaricom new range)."""
        assert format_phone_number("0110345678") == "254110345678"

    def test_invalid_format_raises(self) -> None:
        """Invalid format should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid phone number"):
            format_phone_number("12345")

    def test_invalid_length_raises(self) -> None:
        """Invalid length should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid phone number length"):
            format_phone_number("07123456789999")
