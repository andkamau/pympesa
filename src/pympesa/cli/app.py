"""Main CLI application for pympesa."""

from __future__ import annotations

import sys

import click

from pympesa import Pympesa, __version__
from pympesa.exceptions import PympesaError

from .config import Config
from .output import (
    confirm,
    open_qr_code,
    print_config,
    print_error,
    print_exception,
    print_info,
    print_json,
    print_success,
    print_warning,
    prompt,
    save_qr_code,
)


def get_client(config: Config) -> Pympesa:
    """Create a Pympesa client from configuration.

    Args:
        config: Configuration object.

    Returns:
        Configured Pympesa client.

    Raises:
        click.ClickException: If credentials are missing.
    """
    if not config.has_credentials:
        raise click.ClickException(
            "Missing credentials. Set MPESA_CONSUMER_KEY and MPESA_CONSUMER_SECRET "
            "environment variables, or run 'pympesa init' for setup instructions."
        )

    return Pympesa(
        consumer_key=config.consumer_key,  # type: ignore[arg-type]
        consumer_secret=config.consumer_secret,  # type: ignore[arg-type]
        env=config.environment,
    )


@click.group()
@click.version_option(version=__version__, prog_name="pympesa")
@click.pass_context
def main(ctx: click.Context) -> None:
    """pympesa - M-PESA Daraja API CLI tool.

    A command-line interface for testing and interacting with the
    Safaricom M-PESA Daraja APIs.

    Set your credentials via environment variables:

        export MPESA_CONSUMER_KEY=your_key

        export MPESA_CONSUMER_SECRET=your_secret

    Then configure your settings:

        pympesa init
    """
    ctx.ensure_object(dict)
    ctx.obj["config"] = Config()


# =============================================================================
# init command
# =============================================================================


@main.command()
@click.pass_context
def init(ctx: click.Context) -> None:
    """Initialize pympesa configuration.

    Interactive wizard to set up your M-PESA API configuration.
    Credentials must be set via environment variables.
    """
    config: Config = ctx.obj["config"]

    print_info("pympesa Configuration Wizard")
    print_info("=" * 40)

    # Check for credentials
    if not config.has_credentials:
        print_warning(
            "\nCredentials not found in environment variables.\n"
            "Please set the following before using pympesa:\n"
            "  export MPESA_CONSUMER_KEY=your_consumer_key\n"
            "  export MPESA_CONSUMER_SECRET=your_consumer_secret\n"
            "\nGet your credentials at: https://developer.safaricom.co.ke\n"
        )
    else:
        print_success("Credentials found in environment variables")

    # Environment selection
    env = prompt(
        "\nSelect environment (sandbox/production)",
        default=config.get("environment", "sandbox"),
    )
    if env in ("sandbox", "production"):
        config.set("environment", env)
    else:
        print_warning(f"Invalid environment '{env}', using 'sandbox'")
        config.set("environment", "sandbox")

    # Shortcode
    shortcode = prompt(
        "Business shortcode",
        default=config.get("shortcode", ""),
    )
    if shortcode:
        config.set("shortcode", shortcode)

    # Passkey (for STK Push)
    passkey = prompt(
        "Lipa Na M-PESA passkey (for STK Push)",
        default=config.get("passkey", ""),
    )
    if passkey:
        config.set("passkey", passkey)

    # Callback URLs
    callback_url = prompt(
        "Default callback URL",
        default=config.get("callback_url", ""),
    )
    if callback_url:
        config.set("callback_url", callback_url)

    # Save configuration
    config.save()
    print_success(f"\nConfiguration saved to {config.config_path}")

    # Show current config
    print_info("\nCurrent configuration:")
    print_config(config.to_dict())


# =============================================================================
# auth command
# =============================================================================


@main.command()
@click.pass_context
def auth(ctx: click.Context) -> None:
    """Generate and display an access token.

    Fetches a new OAuth access token using your credentials.
    """
    config: Config = ctx.obj["config"]

    try:
        client = get_client(config)
        token = client._token_manager.get_token()
        print_success("Access token generated successfully")
        print_json({"access_token": token}, title="Token")
    except PympesaError as e:
        print_exception(e)
        sys.exit(1)


# =============================================================================
# stk-push command
# =============================================================================


@main.command("stk-push")
@click.option("--phone", "-p", required=True, help="Phone number (254XXXXXXXXX)")
@click.option("--amount", "-a", required=True, type=int, help="Amount to charge")
@click.option("--reference", "-r", default="Payment", help="Account reference")
@click.option("--description", "-d", default="Payment", help="Transaction description")
@click.option("--callback-url", help="Override default callback URL")
@click.pass_context
def stk_push(
    ctx: click.Context,
    phone: str,
    amount: int,
    reference: str,
    description: str,
    callback_url: str | None,
) -> None:
    """Trigger an STK Push (M-PESA Express) request.

    Initiates a payment prompt on the customer's phone.
    """
    config: Config = ctx.obj["config"]

    # Validate required config
    shortcode = config.get("shortcode")
    passkey = config.get("passkey")
    url = callback_url or config.get("callback_url")

    if not shortcode:
        raise click.ClickException("Shortcode not configured. Run 'pympesa init'")
    if not passkey:
        raise click.ClickException("Passkey not configured. Run 'pympesa init'")
    if not url:
        raise click.ClickException(
            "Callback URL not configured. Run 'pympesa init' or use --callback-url"
        )

    try:
        client = get_client(config)
        response = client.stk_push(
            shortcode=shortcode,
            passkey=passkey,
            amount=amount,
            phone=phone,
            callback_url=url,
            account_reference=reference,
            description=description,
        )
        print_success("STK Push initiated successfully")
        print_json(response, title="Response")
    except PympesaError as e:
        print_exception(e)
        sys.exit(1)


# =============================================================================
# stk-query command
# =============================================================================


@main.command("stk-query")
@click.option("--checkout-id", "-c", required=True, help="CheckoutRequestID from STK Push")
@click.pass_context
def stk_query(ctx: click.Context, checkout_id: str) -> None:
    """Query the status of an STK Push transaction."""
    config: Config = ctx.obj["config"]

    shortcode = config.get("shortcode")
    passkey = config.get("passkey")

    if not shortcode:
        raise click.ClickException("Shortcode not configured. Run 'pympesa init'")
    if not passkey:
        raise click.ClickException("Passkey not configured. Run 'pympesa init'")

    try:
        client = get_client(config)
        response = client.stk_query(
            shortcode=shortcode,
            passkey=passkey,
            checkout_request_id=checkout_id,
        )
        print_success("Query completed")
        print_json(response, title="Response")
    except PympesaError as e:
        print_exception(e)
        sys.exit(1)


# =============================================================================
# c2b-register command
# =============================================================================


@main.command("c2b-register")
@click.option("--confirmation-url", required=True, help="Confirmation callback URL")
@click.option("--validation-url", required=True, help="Validation callback URL")
@click.option("--response-type", default="Completed", help="Response type (Completed/Cancelled)")
@click.pass_context
def c2b_register(
    ctx: click.Context,
    confirmation_url: str,
    validation_url: str,
    response_type: str,
) -> None:
    """Register C2B validation and confirmation URLs."""
    config: Config = ctx.obj["config"]

    shortcode = config.get("shortcode")
    if not shortcode:
        raise click.ClickException("Shortcode not configured. Run 'pympesa init'")

    try:
        client = get_client(config)
        response = client.c2b_register_urls(
            shortcode=shortcode,
            confirmation_url=confirmation_url,
            validation_url=validation_url,
            response_type=response_type,
        )
        print_success("C2B URLs registered successfully")
        print_json(response, title="Response")
    except PympesaError as e:
        print_exception(e)
        sys.exit(1)


# =============================================================================
# c2b-simulate command
# =============================================================================


@main.command("c2b-simulate")
@click.option("--phone", "-p", required=True, help="Phone number (254XXXXXXXXX)")
@click.option("--amount", "-a", required=True, type=int, help="Amount")
@click.option("--reference", "-r", default="", help="Bill reference number")
@click.pass_context
def c2b_simulate(
    ctx: click.Context,
    phone: str,
    amount: int,
    reference: str,
) -> None:
    """Simulate a C2B transaction (sandbox only)."""
    config: Config = ctx.obj["config"]

    shortcode = config.get("shortcode")
    if not shortcode:
        raise click.ClickException("Shortcode not configured. Run 'pympesa init'")

    if config.environment != "sandbox":
        raise click.ClickException("C2B simulation is only available in sandbox environment")

    try:
        client = get_client(config)
        response = client.c2b_simulate(
            shortcode=shortcode,
            phone=phone,
            amount=amount,
            bill_ref_number=reference,
        )
        print_success("C2B simulation completed")
        print_json(response, title="Response")
    except PympesaError as e:
        print_exception(e)
        sys.exit(1)


# =============================================================================
# balance command
# =============================================================================


@main.command()
@click.option("--initiator", "-i", required=True, help="API initiator username")
@click.option("--credential", "-c", required=True, help="Security credential")
@click.option("--result-url", required=True, help="Result callback URL")
@click.option("--timeout-url", required=True, help="Timeout callback URL")
@click.pass_context
def balance(
    ctx: click.Context,
    initiator: str,
    credential: str,
    result_url: str,
    timeout_url: str,
) -> None:
    """Query account balance."""
    config: Config = ctx.obj["config"]

    shortcode = config.get("shortcode")
    if not shortcode:
        raise click.ClickException("Shortcode not configured. Run 'pympesa init'")

    try:
        client = get_client(config)
        response = client.account_balance(
            initiator_name=initiator,
            security_credential=credential,
            shortcode=shortcode,
            result_url=result_url,
            timeout_url=timeout_url,
        )
        print_success("Balance query submitted")
        print_json(response, title="Response")
    except PympesaError as e:
        print_exception(e)
        sys.exit(1)


# =============================================================================
# reversal command
# =============================================================================


@main.command()
@click.option("--initiator", "-i", required=True, help="API initiator username")
@click.option("--credential", "-c", required=True, help="Security credential")
@click.option("--transaction-id", "-t", required=True, help="Transaction ID to reverse")
@click.option("--amount", "-a", required=True, type=int, help="Amount to reverse")
@click.option("--result-url", required=True, help="Result callback URL")
@click.option("--timeout-url", required=True, help="Timeout callback URL")
@click.option("--remarks", default="Reversal", help="Remarks")
@click.pass_context
def reversal(
    ctx: click.Context,
    initiator: str,
    credential: str,
    transaction_id: str,
    amount: int,
    result_url: str,
    timeout_url: str,
    remarks: str,
) -> None:
    """Reverse a transaction."""
    config: Config = ctx.obj["config"]

    shortcode = config.get("shortcode")
    if not shortcode:
        raise click.ClickException("Shortcode not configured. Run 'pympesa init'")

    try:
        client = get_client(config)
        response = client.reversal(
            initiator_name=initiator,
            security_credential=credential,
            shortcode=shortcode,
            transaction_id=transaction_id,
            amount=amount,
            result_url=result_url,
            timeout_url=timeout_url,
            remarks=remarks,
        )
        print_success("Reversal request submitted")
        print_json(response, title="Response")
    except PympesaError as e:
        print_exception(e)
        sys.exit(1)


# =============================================================================
# tax command
# =============================================================================


@main.command()
@click.option("--initiator", "-i", required=True, help="API initiator username")
@click.option("--credential", "-c", required=True, help="Security credential")
@click.option("--amount", "-a", required=True, type=int, help="Tax amount")
@click.option("--prn", required=True, help="Payment Registration Number")
@click.option("--result-url", required=True, help="Result callback URL")
@click.option("--timeout-url", required=True, help="Timeout callback URL")
@click.pass_context
def tax(
    ctx: click.Context,
    initiator: str,
    credential: str,
    amount: int,
    prn: str,
    result_url: str,
    timeout_url: str,
) -> None:
    """Remit tax to KRA."""
    config: Config = ctx.obj["config"]

    shortcode = config.get("shortcode")
    if not shortcode:
        raise click.ClickException("Shortcode not configured. Run 'pympesa init'")

    try:
        client = get_client(config)
        response = client.tax_remittance(
            initiator_name=initiator,
            security_credential=credential,
            sender_shortcode=shortcode,
            amount=amount,
            account_reference=prn,
            result_url=result_url,
            timeout_url=timeout_url,
        )
        print_success("Tax remittance submitted")
        print_json(response, title="Response")
    except PympesaError as e:
        print_exception(e)
        sys.exit(1)


# =============================================================================
# b2b command
# =============================================================================


@main.command()
@click.option("--initiator", "-i", required=True, help="API initiator username")
@click.option("--credential", "-c", required=True, help="Security credential")
@click.option("--receiver", "-r", required=True, help="Receiver shortcode")
@click.option("--amount", "-a", required=True, type=int, help="Amount")
@click.option("--reference", default="", help="Account reference")
@click.option("--result-url", required=True, help="Result callback URL")
@click.option("--timeout-url", required=True, help="Timeout callback URL")
@click.option("--remarks", default="B2B Payment", help="Remarks")
@click.pass_context
def b2b(
    ctx: click.Context,
    initiator: str,
    credential: str,
    receiver: str,
    amount: int,
    reference: str,
    result_url: str,
    timeout_url: str,
    remarks: str,
) -> None:
    """Execute Business to Business payment."""
    config: Config = ctx.obj["config"]

    shortcode = config.get("shortcode")
    if not shortcode:
        raise click.ClickException("Shortcode not configured. Run 'pympesa init'")

    try:
        client = get_client(config)
        response = client.b2b_payment(
            initiator_name=initiator,
            security_credential=credential,
            sender_shortcode=shortcode,
            receiver_shortcode=receiver,
            amount=amount,
            account_reference=reference,
            result_url=result_url,
            timeout_url=timeout_url,
            remarks=remarks,
        )
        print_success("B2B payment submitted")
        print_json(response, title="Response")
    except PympesaError as e:
        print_exception(e)
        sys.exit(1)


# =============================================================================
# dynamic-qr command
# =============================================================================


@main.command("dynamic-qr")
@click.option("--merchant-name", "-m", required=True, help="Merchant name")
@click.option("--ref-no", "-r", required=True, help="Transaction reference number")
@click.option("--amount", "-a", required=True, type=int, help="Amount")
@click.option("--transaction-type", "-t", default="BG", help="Transaction type (BG/PB/SM/SB/WA)")
@click.option("--size", "-s", default="300", help="QR code size in pixels")
@click.option("--output", "-o", default="qr_code.png", help="Output file path for QR image")
@click.option("--open", "should_open", is_flag=True, help="Open the QR code image automatically")
@click.pass_context
def dynamic_qr(
    ctx: click.Context,
    merchant_name: str,
    ref_no: str,
    amount: int,
    transaction_type: str,
    size: str,
    output: str,
    should_open: bool,
) -> None:
    """Generate a dynamic M-PESA QR code and save as image.

    Transaction types:
    - BG: Buy Goods
    - PB: Pay Bill
    - SM: Send Money
    - SB: Send to Business
    - WA: Withdraw Agent
    """
    config: Config = ctx.obj["config"]

    shortcode = config.get("shortcode")
    if not shortcode:
        raise click.ClickException("Shortcode not configured. Run 'pympesa init'")

    try:
        client = get_client(config)
        response = client.dynamic_qr(
            merchant_name=merchant_name,
            ref_no=ref_no,
            amount=amount,
            shortcode=shortcode,
            transaction_type=transaction_type,
            size=size,
        )
        print_success("Dynamic QR code generated successfully")

        # Extract and save the QR code image
        if "QRCode" in response:
            qr_base64 = response["QRCode"]
            try:
                file_path = save_qr_code(qr_base64, output)
                print_success(f"QR code image saved to: {file_path}")

                if should_open:
                    open_qr_code(file_path)
            except ValueError as e:
                print_error(str(e))
        else:
            print_warning("QRCode not found in response")

        # Show response details
        print_json(response, title="Response")
    except PympesaError as e:
        print_exception(e)
        sys.exit(1)


# =============================================================================
# config command
# =============================================================================


@main.command()
@click.option("--show", is_flag=True, help="Show current configuration")
@click.option("--reset", is_flag=True, help="Reset all configuration")
@click.pass_context
def config(ctx: click.Context, show: bool, reset: bool) -> None:
    """Manage CLI configuration."""
    cfg: Config = ctx.obj["config"]

    if reset:
        if confirm("Are you sure you want to reset all configuration?"):
            cfg.clear()
            cfg.save()
            print_success("Configuration reset")
        return

    if show or (not reset):
        print_info(f"Config file: {cfg.config_path}")
        print_info(f"Credentials: {'Set' if cfg.has_credentials else 'Not set'}")
        print_config(cfg.to_dict())


if __name__ == "__main__":
    main()
