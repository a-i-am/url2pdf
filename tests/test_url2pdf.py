"""Tests for url2pdf."""

from __future__ import annotations

import re
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from url2pdf import __version__, make_filename
from url2pdf.cli import build_parser, main
from url2pdf.exceptions import PageLoadError, PDFGenerationError, Url2PdfError


# ---------------------------------------------------------------------------
# Unit tests — no browser needed
# ---------------------------------------------------------------------------

class TestMakeFilename:
    def test_normal_title(self):
        name = make_filename("Hello World")
        assert name.startswith("Hello World_")
        assert name.endswith(".pdf")

    def test_strips_illegal_chars(self):
        name = make_filename('file/with:bad*chars?"<>|')
        assert "/" not in name
        assert ":" not in name
        assert "*" not in name

    def test_empty_title_falls_back(self):
        name = make_filename("")
        assert name.startswith("page_")

    def test_long_title_truncated(self):
        name = make_filename("a" * 200)
        # prefix before timestamp should be at most 60 chars
        prefix = name.rsplit("_", 2)[0]
        assert len(prefix) <= 60

    def test_timestamp_format(self):
        name = make_filename("test")
        # ends with _YYYYMMDD_HHMMSS.pdf
        assert re.search(r"_\d{8}_\d{6}\.pdf$", name)


class TestExceptions:
    def test_hierarchy(self):
        assert issubclass(PageLoadError, Url2PdfError)
        assert issubclass(PDFGenerationError, Url2PdfError)

    def test_message(self):
        exc = PageLoadError("bad url")
        assert "bad url" in str(exc)


class TestCLIParser:
    def setup_method(self):
        self.parser = build_parser()

    def test_url_required(self):
        with pytest.raises(SystemExit):
            self.parser.parse_args([])

    def test_defaults(self):
        args = self.parser.parse_args(["https://example.com"])
        assert args.url == "https://example.com"
        assert args.output is None
        assert args.format == "A4"
        assert args.scale == 0.9
        assert args.timeout == 60
        assert args.scroll_rounds == 80
        assert args.quiet is False

    def test_short_flags(self):
        args = self.parser.parse_args(["https://x.com", "-o", "out.pdf", "-q"])
        assert args.output == "out.pdf"
        assert args.quiet is True

    def test_long_flags(self):
        args = self.parser.parse_args([
            "https://x.com",
            "--format", "Letter",
            "--scale", "0.8",
            "--timeout", "30",
            "--scroll-rounds", "10",
        ])
        assert args.format == "Letter"
        assert args.scale == 0.8
        assert args.timeout == 30
        assert args.scroll_rounds == 10


class TestCLIMain:
    def test_invalid_scale_exits_nonzero(self):
        with pytest.raises(SystemExit) as exc_info:
            main(["https://example.com", "--scale", "5.0"])
        assert exc_info.value.code != 0

    def test_page_load_error_returns_1(self):
        with patch("url2pdf.cli.convert", side_effect=PageLoadError("timeout")):
            code = main(["https://example.com"])
        assert code == 1

    def test_success_returns_0(self, tmp_path):
        out = tmp_path / "out.pdf"
        with patch("url2pdf.cli.convert", return_value=out):
            code = main(["https://example.com", "-o", str(out)])
        assert code == 0

    def test_keyboard_interrupt_returns_130(self):
        with patch("url2pdf.cli.convert", side_effect=KeyboardInterrupt):
            code = main(["https://example.com"])
        assert code == 130


class TestVersion:
    def test_semver_format(self):
        assert re.match(r"^\d+\.\d+\.\d+", __version__)
