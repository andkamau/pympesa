"""Custom exceptions for pympesa library."""

from __future__ import annotations

from typing import Any


class PympesaError(Exception):
    """Base exception for all pympesa errors."""

    pass


class ConfigurationError(PympesaError):
    """Raised when there's a configuration problem."""

    pass


class AuthenticationError(PympesaError):
    """Raised when authentication fails."""

    def __init__(
        self,
        message: str = "Authentication failed",
        status_code: int | None = None,
        response_data: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data or {}


class APIError(PympesaError):
    """Raised when an API request fails."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_data: dict[str, Any] | None = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data or {}
        self.request_id = request_id

    def __str__(self) -> str:
        parts = [super().__str__()]
        if self.status_code:
            parts.append(f"(HTTP {self.status_code})")
        if self.request_id:
            parts.append(f"[Request ID: {self.request_id}]")
        return " ".join(parts)


class ValidationError(PympesaError):
    """Raised when request validation fails."""

    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(message)
        self.field = field
