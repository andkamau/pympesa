# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

pympesa is a modern Python client library for Safaricom's M-PESA Daraja API. It provides a clean interface for integrating mobile money transactions into Python applications, supporting the full range of M-PESA operations including STK Push, C2B, B2C, B2B, reversals, balance queries, tax remittance, and dynamic QR code generation.

**Version:** 2.0.0
**Python:** 3.9+

## Project Structure

```
pympesa/
├── pyproject.toml           # Package configuration (PEP 621)
├── README.md                # Documentation
├── CHANGELOG.md             # Version history
├── LICENSE.txt              # MIT License
├── src/pympesa/             # Main package (src layout)
│   ├── __init__.py          # Public API exports
│   ├── client.py            # Pympesa client class
│   ├── auth.py              # TokenManager (auto-refresh)
│   ├── endpoints.py         # URL registry
│   ├── exceptions.py        # Custom exceptions
│   ├── utils.py             # Helpers (timestamps, passwords)
│   └── cli/                 # CLI tool
│       ├── __init__.py
│       ├── app.py           # Click commands
│       ├── config.py        # Config management
│       └── output.py        # Rich output formatting
└── tests/                   # pytest test suite
    ├── conftest.py          # Shared fixtures
    ├── test_auth.py
    ├── test_client.py
    ├── test_cli.py
    ├── test_output.py
    └── test_utils.py
```

## Development Commands

### Installation
```bash
# Create virtual environment
python -m venv .venv-pympesa
source .venv-pympesa/bin/activate

# Install with all dependencies
pip install -e ".[dev,cli]"
```

### Running Tests
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=pympesa --cov-report=html

# Run specific test file
pytest tests/test_client.py -v
```

### Package Building
```bash
python -m build
```

## Code Architecture

### Core Components

**Pympesa** (`src/pympesa/client.py`): Main client class with methods for all M-PESA API operations. Automatically manages OAuth tokens via TokenManager.

**TokenManager** (`src/pympesa/auth.py`): Handles OAuth token generation, caching, and automatic refresh (5-minute buffer before expiry).

**Endpoints** (`src/pympesa/endpoints.py`): URL registry for sandbox and production environments.

**Exceptions** (`src/pympesa/exceptions.py`): Custom exception hierarchy (PympesaError, APIError, AuthenticationError, ValidationError).

### API Flow Pattern

```python
from pympesa import Pympesa

# Client handles token management automatically
client = Pympesa(
    consumer_key="your_key",
    consumer_secret="your_secret",
    env="sandbox"  # or "production"
)

# All methods return parsed JSON dicts
response = client.stk_push(
    shortcode="174379",
    passkey="...",
    amount=100,
    phone="254712345678",
    callback_url="https://...",
    account_reference="Order123",
    description="Payment"
)
```

### CLI Tool

The CLI uses Click for commands and Rich for output formatting:

```bash
# Setup
pympesa init

# Generate token
pympesa auth

# STK Push
pympesa stk-push --phone 254712345678 --amount 100

# Generate QR code
pympesa dynamic-qr --merchant-name "Store" --ref-no "INV001" --amount 500 --open
```

Credentials are read from environment variables:
- `MPESA_CONSUMER_KEY`
- `MPESA_CONSUMER_SECRET`

Config stored in `~/.pympesa/config.json` (non-sensitive settings only).

## Testing Approach

- **Framework:** pytest with pytest-mock and responses
- **Coverage target:** 90%+
- **All API calls mocked** - no live API calls in tests
- **Fixtures in conftest.py** for shared test data

## Important Notes

- OAuth tokens auto-refresh 5 minutes before expiry
- Phone numbers auto-formatted to 254XXXXXXXXX
- C2B simulate only works in sandbox
- QR code images saved as PNG files
- All methods return parsed JSON dicts (not Response objects)
