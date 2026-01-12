# pympesa

Modern Python client for the Safaricom M-PESA Daraja API.

[![PyPI version](https://badge.fury.io/py/pympesa.svg)](https://badge.fury.io/py/pympesa)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- **Complete API Coverage**: STK Push, C2B, B2C, B2B, Reversals, Balance queries, and more
- **Automatic Token Management**: Handles OAuth token refresh automatically
- **Type Hints**: Full type annotations for better IDE support
- **CLI Tool**: Interactive command-line interface for testing and quick operations
- **Modern Python**: Built for Python 3.10+ with modern best practices

## Installation

### Library Only

```bash
pip install pympesa
```

### With CLI Tool

```bash
pip install pympesa[cli]
```

## Quick Start

### Library Usage

```python
from pympesa import Pympesa

# Initialize client
client = Pympesa(
    consumer_key="your_consumer_key",
    consumer_secret="your_consumer_secret",
    env="sandbox"  # or "production"
)

# Initiate STK Push
response = client.stk_push(
    shortcode="174379",
    passkey="your_passkey",
    amount=100,
    phone="254712345678",
    callback_url="https://example.com/callback",
    account_reference="Order123",
    description="Payment for order"
)

print(response)
# {'MerchantRequestID': '...', 'CheckoutRequestID': '...', 'ResponseCode': '0', ...}
```

### CLI Usage

First, set your credentials as environment variables:

```bash
export MPESA_CONSUMER_KEY=your_consumer_key
export MPESA_CONSUMER_SECRET=your_consumer_secret
```

Then configure the CLI:

```bash
pympesa init
```

Now you can use the CLI commands:

```bash
# Generate access token
pympesa auth

# Initiate STK Push
pympesa stk-push --phone 254712345678 --amount 100

# Query STK Push status
pympesa stk-query --checkout-id ws_CO_123456789

# View configuration
pympesa config --show
```

## API Reference

### Pympesa Client

```python
from pympesa import Pympesa, Environment

client = Pympesa(
    consumer_key="your_key",
    consumer_secret="your_secret",
    env=Environment.SANDBOX,  # or Environment.PRODUCTION
    timeout=30  # request timeout in seconds
)
```

### Available Methods

#### STK Push (M-PESA Express)

```python
# Initiate payment
response = client.stk_push(
    shortcode="174379",
    passkey="your_passkey",
    amount=100,
    phone="254712345678",
    callback_url="https://example.com/callback",
    account_reference="Order123",
    description="Payment",
    transaction_type="CustomerPayBillOnline"  # or "CustomerBuyGoodsOnline"
)

# Query status
status = client.stk_query(
    shortcode="174379",
    passkey="your_passkey",
    checkout_request_id="ws_CO_123456789"
)
```

#### C2B (Customer to Business)

```python
# Register URLs
client.c2b_register_urls(
    shortcode="600000",
    confirmation_url="https://example.com/confirm",
    validation_url="https://example.com/validate",
    response_type="Completed"  # or "Cancelled"
)

# Simulate (sandbox only)
client.c2b_simulate(
    shortcode="600000",
    phone="254712345678",
    amount=100,
    bill_ref_number="INV001"
)
```

#### B2C (Business to Customer)

```python
response = client.b2c_payment(
    initiator_name="testapi",
    security_credential="encrypted_credential",
    shortcode="600000",
    phone="254712345678",
    amount=100,
    result_url="https://example.com/result",
    timeout_url="https://example.com/timeout",
    command_id="BusinessPayment",
    remarks="Salary payment"
)
```

#### B2B (Business to Business)

```python
response = client.b2b_payment(
    initiator_name="testapi",
    security_credential="encrypted_credential",
    sender_shortcode="600000",
    receiver_shortcode="600001",
    amount=1000,
    result_url="https://example.com/result",
    timeout_url="https://example.com/timeout",
    command_id="BusinessPayBill",
    account_reference="INV001"
)
```

#### Account Balance

```python
response = client.account_balance(
    initiator_name="testapi",
    security_credential="encrypted_credential",
    shortcode="600000",
    result_url="https://example.com/result",
    timeout_url="https://example.com/timeout"
)
```

#### Transaction Status

```python
response = client.transaction_status(
    initiator_name="testapi",
    security_credential="encrypted_credential",
    shortcode="600000",
    transaction_id="OEI2AK4Q16",
    result_url="https://example.com/result",
    timeout_url="https://example.com/timeout"
)
```

#### Reversal

```python
response = client.reversal(
    initiator_name="testapi",
    security_credential="encrypted_credential",
    shortcode="600000",
    transaction_id="OEI2AK4Q16",
    amount=100,
    result_url="https://example.com/result",
    timeout_url="https://example.com/timeout"
)
```

#### Tax Remittance

```python
response = client.tax_remittance(
    initiator_name="testapi",
    security_credential="encrypted_credential",
    sender_shortcode="600000",
    amount=500,
    account_reference="PRN123456",
    result_url="https://example.com/result",
    timeout_url="https://example.com/timeout"
)
```

#### Dynamic QR Code

```python
from pympesa import Pympesa
from pympesa.cli.output import save_qr_code

client = Pympesa(...)
response = client.dynamic_qr(
    merchant_name="My Store",
    ref_no="INV123",
    amount=100,
    shortcode="174379",
    transaction_type="BG",  # BG=Buy Goods, PB=Pay Bill
    size="300"
)

# Save the QR code image to a file
if "QRCode" in response:
    file_path = save_qr_code(response["QRCode"], "my_qr_code.png")
    print(f"QR code saved to: {file_path}")
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `pympesa init` | Interactive setup wizard |
| `pympesa auth` | Generate and display access token |
| `pympesa stk-push` | Initiate STK Push payment |
| `pympesa stk-query` | Query STK Push status |
| `pympesa c2b-register` | Register C2B URLs |
| `pympesa c2b-simulate` | Simulate C2B transaction (sandbox) |
| `pympesa balance` | Query account balance |
| `pympesa reversal` | Reverse a transaction |
| `pympesa tax` | Remit tax to KRA |
| `pympesa b2b` | B2B payment |
| `pympesa dynamic-qr` | Generate a dynamic M-PESA QR code |
| `pympesa config` | View/manage configuration |

Use `pympesa <command> --help` for detailed options.

### CLI Examples

**Generate a QR code and save as image:**
```bash
pympesa dynamic-qr \
  --merchant-name "My Store" \
  --ref-no "INV001" \
  --amount 500 \
  --transaction-type BG \
  --output qr_code.png \
  --open  # Opens the QR code image automatically
```

The `--open` flag will automatically open the generated QR code image in your default image viewer (macOS, Linux, or Windows).

## Environment Variables

| Variable | Description |
|----------|-------------|
| `MPESA_CONSUMER_KEY` | Your M-PESA API consumer key |
| `MPESA_CONSUMER_SECRET` | Your M-PESA API consumer secret |

## Configuration File

The CLI stores non-sensitive configuration in `~/.pympesa/config.json`:

```json
{
  "environment": "sandbox",
  "shortcode": "174379",
  "passkey": "your_passkey",
  "callback_url": "https://example.com/callback"
}
```

**Note**: Credentials are never stored in the config file. Always use environment variables.

## Error Handling

```python
from pympesa import Pympesa, PympesaError, APIError, AuthenticationError

try:
    response = client.stk_push(...)
except AuthenticationError as e:
    print(f"Auth failed: {e}")
except APIError as e:
    print(f"API error: {e}")
    print(f"Status code: {e.status_code}")
    print(f"Response: {e.response_data}")
except PympesaError as e:
    print(f"Error: {e}")
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/pythias-io/pympesa.git
cd pympesa

# Create virtual environment
python -m venv .venv-pympesa
source .venv-pympesa/bin/activate

# Install with dev dependencies
pip install -e ".[dev,cli]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pympesa --cov-report=html

# Run specific test file
pytest tests/test_client.py -v
```

## Getting Credentials

1. Go to [Safaricom Developer Portal](https://developer.safaricom.co.ke/)
2. Create an account and log in
3. Create a new app to get your Consumer Key and Consumer Secret
4. Use sandbox credentials for testing, production for live transactions

## License

MIT License - see [LICENSE.txt](LICENSE.txt) for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Links

- [Safaricom Developer Portal](https://developer.safaricom.co.ke/)
- [M-PESA API Documentation](https://developer.safaricom.co.ke/Documentation)
- [GitHub Repository](https://github.com/pythias-io/pympesa)
- [PyPI Package](https://pypi.org/project/pympesa/)
