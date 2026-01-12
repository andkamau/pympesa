"""Output formatting for pympesa CLI using Rich."""

from __future__ import annotations

import base64
import json
import subprocess
import sys
import traceback
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

# Console instances for stdout and stderr
console = Console()
error_console = Console(stderr=True)


def print_success(message: str) -> None:
    """Print a success message.

    Args:
        message: The success message to display.
    """
    console.print(f"[bold green]✓[/bold green] {message}")


def print_error(message: str) -> None:
    """Print an error message.

    Args:
        message: The error message to display.
    """
    error_console.print(f"[bold red]✗[/bold red] {message}")


def print_warning(message: str) -> None:
    """Print a warning message.

    Args:
        message: The warning message to display.
    """
    console.print(f"[bold yellow]![/bold yellow] {message}")


def print_info(message: str) -> None:
    """Print an info message.

    Args:
        message: The info message to display.
    """
    console.print(f"[bold blue]ℹ[/bold blue] {message}")


def print_json(data: dict[str, Any], title: str | None = None) -> None:
    """Print JSON data with syntax highlighting.

    Args:
        data: The JSON data to display.
        title: Optional title for the panel.
    """
    json_str = json.dumps(data, indent=2, default=str)
    syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)

    if title:
        console.print(Panel(syntax, title=title, border_style="green"))
    else:
        console.print(syntax)


def print_config(config_data: dict[str, Any]) -> None:
    """Print configuration in a formatted table.

    Args:
        config_data: Configuration dictionary to display.
    """
    table = Table(title="Current Configuration", show_header=True, header_style="bold cyan")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    for key, value in sorted(config_data.items()):
        # Mask sensitive values
        display_value = str(value)
        if "secret" in key.lower() or "password" in key.lower() or "key" in key.lower():
            display_value = "****" + display_value[-4:] if len(display_value) > 4 else "****"
        table.add_row(key, display_value)

    console.print(table)


def print_exception(exc: Exception, verbose: bool = False) -> None:
    """Print an exception with optional traceback.

    Args:
        exc: The exception to display.
        verbose: Whether to show full traceback.
    """
    print_error(str(exc))

    # Show additional details for API errors
    if hasattr(exc, "status_code") and exc.status_code:
        error_console.print(f"  [dim]HTTP Status:[/dim] {exc.status_code}")

    if hasattr(exc, "response_data") and exc.response_data:
        error_console.print("  [dim]Response:[/dim]")
        json_str = json.dumps(exc.response_data, indent=2)
        error_console.print(Syntax(json_str, "json", theme="monokai"))

    if verbose:
        error_console.print("\n[dim]Traceback:[/dim]")
        error_console.print(traceback.format_exc())


def confirm(message: str, default: bool = False) -> bool:
    """Ask for confirmation.

    Args:
        message: The confirmation message.
        default: Default value if user just presses Enter.

    Returns:
        True if user confirmed, False otherwise.
    """
    suffix = "[Y/n]" if default else "[y/N]"
    response = console.input(f"{message} {suffix} ").strip().lower()

    if not response:
        return default
    return response in ("y", "yes")


def prompt(message: str, default: str | None = None, password: bool = False) -> str:
    """Prompt for user input.

    Args:
        message: The prompt message.
        default: Default value if user just presses Enter.
        password: Whether to hide input (for sensitive data).

    Returns:
        User input or default value.
    """
    if default:
        message = f"{message} [{default}]"

    response = console.input(f"{message}: ", password=password).strip()

    if not response and default:
        return default
    return response


def save_qr_code(base64_data: str, output_path: str | None = None) -> str:
    """Save a base64-encoded QR code to an image file.

    Args:
        base64_data: Base64-encoded image data from M-PESA API.
        output_path: Optional path to save the image. Defaults to ./qr_code.png

    Returns:
        Path to the saved image file.

    Raises:
        ValueError: If base64 data is invalid.
    """
    if not output_path:
        output_path = "qr_code.png"

    output_file = Path(output_path)

    try:
        # Decode base64 to bytes
        image_data = base64.b64decode(base64_data)

        # Write to file
        with open(output_file, "wb") as f:
            f.write(image_data)

        return str(output_file.absolute())
    except Exception as e:
        raise ValueError(f"Failed to decode QR code: {e}") from e


def open_qr_code(file_path: str) -> None:
    """Open a QR code image in the default image viewer.

    Args:
        file_path: Path to the image file.
    """
    try:
        # macOS
        subprocess.run(["open", file_path], check=False)
    except FileNotFoundError:
        try:
            # Linux
            subprocess.run(["xdg-open", file_path], check=False)
        except FileNotFoundError:
            try:
                # Windows
                subprocess.run(["start", file_path], check=False)
            except FileNotFoundError:
                print_warning(
                    f"Could not open image automatically. "
                    f"Image saved to: {file_path}"
                )
