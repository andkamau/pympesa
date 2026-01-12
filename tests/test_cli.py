"""Tests for pympesa CLI."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from pympesa.cli.app import main
from pympesa.cli.config import Config


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def temp_config_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary config directory."""
    config_dir = tmp_path / ".pympesa"
    config_dir.mkdir()
    yield config_dir


@pytest.fixture
def temp_config(temp_config_dir: Path) -> Config:
    """Create a Config instance with temp directory."""
    return Config(config_path=temp_config_dir / "config.json")


class TestCLIHelp:
    """Tests for CLI help and version."""

    def test_help(self, cli_runner: CliRunner) -> None:
        """Should display help text."""
        result = cli_runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "M-PESA Daraja API CLI tool" in result.output

    def test_version(self, cli_runner: CliRunner) -> None:
        """Should display version."""
        result = cli_runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "2.0.0" in result.output


class TestInitCommand:
    """Tests for init command."""

    def test_init_prompts_for_config(
        self,
        cli_runner: CliRunner,
        temp_config_dir: Path,
    ) -> None:
        """Init should prompt for configuration."""
        with patch("pympesa.cli.app.Config") as MockConfig:
            mock_config = MagicMock()
            mock_config.has_credentials = False
            mock_config.get.return_value = ""
            mock_config.config_path = temp_config_dir / "config.json"
            mock_config.to_dict.return_value = {}
            MockConfig.return_value = mock_config

            result = cli_runner.invoke(
                main,
                ["init"],
                input="sandbox\n174379\ntestpasskey\nhttps://example.com/callback\n",
            )

            assert result.exit_code == 0
            assert mock_config.save.called


class TestAuthCommand:
    """Tests for auth command."""

    def test_auth_without_credentials(self, cli_runner: CliRunner) -> None:
        """Auth should fail without credentials."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("pympesa.cli.app.Config") as MockConfig:
                mock_config = MagicMock()
                mock_config.has_credentials = False
                MockConfig.return_value = mock_config

                result = cli_runner.invoke(main, ["auth"])

                assert result.exit_code != 0
                assert "Missing credentials" in result.output

    def test_auth_with_credentials(self, cli_runner: CliRunner) -> None:
        """Auth should succeed with credentials."""
        with patch("pympesa.cli.app.Config") as MockConfig:
            mock_config = MagicMock()
            mock_config.has_credentials = True
            mock_config.consumer_key = "test_key"
            mock_config.consumer_secret = "test_secret"
            mock_config.environment = "sandbox"
            MockConfig.return_value = mock_config

            with patch("pympesa.cli.app.get_client") as mock_get_client:
                mock_client = MagicMock()
                mock_client._token_manager.get_token.return_value = "test_token_123"
                mock_get_client.return_value = mock_client

                result = cli_runner.invoke(main, ["auth"])

                assert result.exit_code == 0
                assert "test_token_123" in result.output


class TestSTKPushCommand:
    """Tests for stk-push command."""

    def test_stk_push_missing_config(self, cli_runner: CliRunner) -> None:
        """STK push should fail without shortcode config."""
        with patch("pympesa.cli.app.Config") as MockConfig:
            mock_config = MagicMock()
            mock_config.has_credentials = True
            mock_config.get.return_value = None  # No shortcode
            MockConfig.return_value = mock_config

            result = cli_runner.invoke(
                main,
                ["stk-push", "--phone", "254712345678", "--amount", "100"],
            )

            assert result.exit_code != 0
            assert "Shortcode not configured" in result.output

    def test_stk_push_success(self, cli_runner: CliRunner) -> None:
        """STK push should succeed with valid config."""
        with patch("pympesa.cli.app.Config") as MockConfig:
            mock_config = MagicMock()
            mock_config.has_credentials = True
            mock_config.consumer_key = "test_key"
            mock_config.consumer_secret = "test_secret"
            mock_config.environment = "sandbox"
            mock_config.get.side_effect = lambda k, d=None: {
                "shortcode": "174379",
                "passkey": "testpasskey",
                "callback_url": "https://example.com/callback",
            }.get(k, d)
            MockConfig.return_value = mock_config

            with patch("pympesa.cli.app.get_client") as mock_get_client:
                mock_client = MagicMock()
                mock_client.stk_push.return_value = {
                    "ResponseCode": "0",
                    "CheckoutRequestID": "ws_CO_123",
                }
                mock_get_client.return_value = mock_client

                result = cli_runner.invoke(
                    main,
                    ["stk-push", "--phone", "254712345678", "--amount", "100"],
                )

                assert result.exit_code == 0
                assert "STK Push initiated successfully" in result.output


class TestConfigCommand:
    """Tests for config command."""

    def test_config_show(self, cli_runner: CliRunner) -> None:
        """Config show should display configuration."""
        with patch("pympesa.cli.app.Config") as MockConfig:
            mock_config = MagicMock()
            mock_config.has_credentials = True
            mock_config.config_path = Path("/tmp/.pympesa/config.json")
            mock_config.to_dict.return_value = {
                "environment": "sandbox",
                "shortcode": "174379",
            }
            MockConfig.return_value = mock_config

            result = cli_runner.invoke(main, ["config", "--show"])

            assert result.exit_code == 0
            assert "sandbox" in result.output

    def test_config_reset(self, cli_runner: CliRunner) -> None:
        """Config reset should clear configuration."""
        with patch("pympesa.cli.app.Config") as MockConfig:
            mock_config = MagicMock()
            mock_config.has_credentials = False
            mock_config.config_path = Path("/tmp/.pympesa/config.json")
            mock_config.to_dict.return_value = {}
            MockConfig.return_value = mock_config

            result = cli_runner.invoke(main, ["config", "--reset"], input="y\n")

            assert result.exit_code == 0
            assert mock_config.clear.called
            assert mock_config.save.called


class TestDynamicQRCommand:
    """Tests for dynamic-qr command."""

    def test_dynamic_qr_missing_config(self, cli_runner: CliRunner) -> None:
        """Dynamic QR should fail without shortcode config."""
        with patch("pympesa.cli.app.Config") as MockConfig:
            mock_config = MagicMock()
            mock_config.has_credentials = True
            mock_config.get.return_value = None  # No shortcode
            MockConfig.return_value = mock_config

            result = cli_runner.invoke(
                main,
                [
                    "dynamic-qr",
                    "--merchant-name",
                    "Test Store",
                    "--ref-no",
                    "INV123",
                    "--amount",
                    "100",
                ],
            )

            assert result.exit_code != 0
            assert "Shortcode not configured" in result.output

    def test_dynamic_qr_success(self, cli_runner: CliRunner) -> None:
        """Dynamic QR should succeed with valid config."""
        with patch("pympesa.cli.app.Config") as MockConfig:
            mock_config = MagicMock()
            mock_config.has_credentials = True
            mock_config.consumer_key = "test_key"
            mock_config.consumer_secret = "test_secret"
            mock_config.environment = "sandbox"
            mock_config.get.return_value = "174379"  # shortcode
            MockConfig.return_value = mock_config

            with patch("pympesa.cli.app.get_client") as mock_get_client:
                mock_client = MagicMock()
                mock_client.dynamic_qr.return_value = {
                    "ResponseCode": "00",
                    "RequestID": "12345",
                    "QRCode": "base64encodedqrcode...",
                    "ResponseDescription": "The service request is processed successfully.",
                }
                mock_get_client.return_value = mock_client

                result = cli_runner.invoke(
                    main,
                    [
                        "dynamic-qr",
                        "--merchant-name",
                        "Test Store",
                        "--ref-no",
                        "INV123",
                        "--amount",
                        "100",
                    ],
                )

                assert result.exit_code == 0
                assert "Dynamic QR code generated successfully" in result.output
                assert "QRCode" in result.output


class TestConfig:
    """Tests for Config class."""

    def test_config_save_and_load(self, temp_config_dir: Path) -> None:
        """Config should save and load correctly."""
        config_path = temp_config_dir / "config.json"

        # Create and save config
        config = Config(config_path=config_path)
        config.set("environment", "sandbox")
        config.set("shortcode", "174379")
        config.save()

        # Load in new instance
        config2 = Config(config_path=config_path)
        assert config2.get("environment") == "sandbox"
        assert config2.get("shortcode") == "174379"

    def test_config_disallows_credentials(self, temp_config_dir: Path) -> None:
        """Config should not allow storing credentials."""
        config = Config(config_path=temp_config_dir / "config.json")

        with pytest.raises(ValueError, match="cannot be stored"):
            config.set("consumer_key", "secret")

    def test_config_reads_credentials_from_env(
        self,
        temp_config_dir: Path,
    ) -> None:
        """Config should read credentials from environment."""
        with patch.dict(os.environ, {
            "MPESA_CONSUMER_KEY": "test_key",
            "MPESA_CONSUMER_SECRET": "test_secret",
        }):
            config = Config(config_path=temp_config_dir / "config.json")
            assert config.consumer_key == "test_key"
            assert config.consumer_secret == "test_secret"
            assert config.has_credentials is True

    def test_config_has_credentials_false(self, temp_config_dir: Path) -> None:
        """has_credentials should be False when not set."""
        with patch.dict(os.environ, {}, clear=True):
            # Clear any existing env vars
            os.environ.pop("MPESA_CONSUMER_KEY", None)
            os.environ.pop("MPESA_CONSUMER_SECRET", None)

            config = Config(config_path=temp_config_dir / "config.json")
            assert config.has_credentials is False
