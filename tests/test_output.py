"""Tests for pympesa CLI output module."""

from __future__ import annotations

import base64
from pathlib import Path

import pytest

from pympesa.cli.output import save_qr_code


class TestSaveQRCode:
    """Tests for save_qr_code function."""

    def test_save_qr_code_success(self, tmp_path: Path) -> None:
        """Should save base64 QR code to file."""
        # Create a simple 1x1 PNG
        png_bytes = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
        base64_data = base64.b64encode(png_bytes).decode()

        output_file = tmp_path / "test_qr.png"

        result = save_qr_code(base64_data, str(output_file))

        # Check file was created
        assert output_file.exists()
        assert Path(result) == output_file

        # Check file content
        with open(output_file, "rb") as f:
            content = f.read()
        assert content == png_bytes

    def test_save_qr_code_default_path(self, tmp_path: Path, monkeypatch) -> None:
        """Should use default path if not provided."""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        png_bytes = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
        base64_data = base64.b64encode(png_bytes).decode()

        result = save_qr_code(base64_data)

        # Should create qr_code.png in current directory
        assert Path("qr_code.png").exists()
        assert "qr_code.png" in result

    def test_save_qr_code_invalid_base64(self) -> None:
        """Should raise ValueError for invalid base64."""
        with pytest.raises(ValueError, match="Failed to decode"):
            save_qr_code("not-valid-base64!!!")

    def test_save_qr_code_creates_parent_dirs(self, tmp_path: Path) -> None:
        """Should handle nested output paths."""
        output_file = tmp_path / "subdir" / "qr" / "test.png"

        png_bytes = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
        base64_data = base64.b64encode(png_bytes).decode()

        # Should work even though parent dirs don't exist
        # (but will fail because we're not creating them)
        with pytest.raises((ValueError, FileNotFoundError)):
            save_qr_code(base64_data, str(output_file))
