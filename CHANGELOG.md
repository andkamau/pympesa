# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-01-12

### Changed
- **Complete rewrite** of the library from scratch
- Minimum Python version is now **3.10+** (was 3.6+)
- Modern project structure using `src/` layout
- Replaced `setup.py` with `pyproject.toml` (PEP 621)
- All API methods now return parsed JSON dictionaries instead of raw Response objects

### Added
- **CLI Tool**: New command-line interface for interacting with M-PESA APIs
  - `pympesa init` - Interactive setup wizard
  - `pympesa auth` - Generate access tokens
  - `pympesa stk-push` - Initiate STK Push
  - `pympesa stk-query` - Query STK status
  - `pympesa c2b-register` - Register C2B URLs
  - `pympesa c2b-simulate` - Simulate C2B (sandbox)
  - `pympesa balance` - Query account balance
  - `pympesa reversal` - Reverse transactions
  - `pympesa tax` - Tax remittance to KRA
  - `pympesa b2b` - B2B payments
  - `pympesa config` - Manage configuration
- **TokenManager**: Automatic OAuth token management with caching and refresh
- **New endpoints**:
  - Dynamic QR code generation (`dynamic_qr`)
  - Tax remittance (`tax_remittance`)
- **Type hints**: Full type annotations throughout the codebase
- **Custom exceptions**: `PympesaError`, `APIError`, `AuthenticationError`, `ValidationError`, `ConfigurationError`
- **Phone number formatting**: Automatic conversion to 254XXXXXXXXX format
- **Comprehensive test suite**: pytest-based tests with mocking
- **Rich CLI output**: Colored, formatted output using Rich library

### Fixed
- Typo in method name: `transation_status_request` → `transaction_status`
- Typo in parameter: `Occassion` → `Occasion`
- Typo in parameter: `RecieverIdentifierType` → `ReceiverIdentifierType`

### Removed
- Support for Python 3.6-3.9
- Legacy `setup.py` packaging
- Raw `requests.Response` return types (now returns parsed dicts)
- `oauth_generate_token()` standalone function (use `TokenManager` or `Pympesa` client)
- `process_kwargs()` internal function
- `encode_password()` function (replaced by `generate_password()`)

### Migration Guide

#### From 1.x to 2.0

**1. Update imports:**
```python
# Old
from pympesa import Pympesa, oauth_generate_token

# New
from pympesa import Pympesa  # Token management is automatic
```

**2. Update client initialization:**
```python
# Old
token = oauth_generate_token(key, secret)
client = Pympesa(token, env="sandbox")

# New
client = Pympesa(
    consumer_key=key,
    consumer_secret=secret,
    env="sandbox"
)
# Token is managed automatically
```

**3. Update method calls:**
```python
# Old - returns requests.Response
response = client.lipa_na_mpesa_online_payment(**kwargs)
data = response.json()

# New - returns dict directly
data = client.stk_push(
    shortcode="174379",
    passkey="...",
    amount=100,
    phone="254712345678",
    callback_url="https://...",
    account_reference="...",
    description="..."
)
```

**4. Update error handling:**
```python
# Old
if response.status_code != 200:
    print("Error")

# New
from pympesa import APIError
try:
    response = client.stk_push(...)
except APIError as e:
    print(f"Error: {e}, Status: {e.status_code}")
```

## [1.0.2] - 2023-XX-XX

- Last version before 2.0 rewrite
- Migrated to Python 3
- Basic M-PESA API support

## [1.0.0] - Initial Release

- Initial release with basic M-PESA Daraja API support
