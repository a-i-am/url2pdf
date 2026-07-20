"""Tests for url2pdf."""

from __future__ import annotations

import re
from unittest.mock import MagicMock, patch

import pytest

from url2pdf import __version__, make_filename
from url2pdf.cli import build_parser, main
from url2pdf.converter import (
    _JS_DISMISS_OVERLAYS,
    _JS_LINEARIZE_RECRUIT_PAGE,
    _JS_PREPARE_FOR_PRINT,
    _OCR_FONT_CANDIDATES,
    _PRINT_CSS,
    _find_ocr_fontfile,
    _normalize_ocr_text,
    _ocr_text_runs,
    convert,
    wait_for_manual_verification,
)
from url2pdf.exceptions import PageLoadError, PDFGenerationError, Url2PdfError
from url2pdf.gui import Url2PdfApp

# ---------------------------------------------------------------------------
# Unit tests - no browser needed
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
        with pytest.raises(SystemExit) as exc:
            from url2pdf.cli import main
            main([])
        assert exc.value.code != 0

    def test_defaults(self):
        args = self.parser.parse_args(["https://example.com"])
        assert args.url == "https://example.com"
        assert args.output is None
        assert args.format == "A4"
        assert args.scale == 0.9
        assert args.pdf_layout == "pages"
        assert args.timeout == 60
        assert args.scroll_rounds == 80
        assert args.headed is False
        assert args.manual_verification is False
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
            "--pdf-layout", "single",
        ])
        assert args.format == "Letter"
        assert args.scale == 0.8
        assert args.timeout == 30
        assert args.scroll_rounds == 10
        assert args.pdf_layout == "single"

    def test_browser_flags(self):
        args = self.parser.parse_args([
            "https://x.com",
            "--headed",
            "--manual-verification",
        ])
        assert args.headed is True
        assert args.manual_verification is True


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

    def test_browser_flags_passed_to_convert(self, tmp_path):
        out = tmp_path / "out.pdf"
        with patch("url2pdf.cli.convert", return_value=out) as mocked_convert:
            code = main([
                "https://example.com",
                "-o",
                str(out),
                "--headed",
                "--manual-verification",
            ])
        assert code == 0
        assert mocked_convert.call_args.kwargs["headless"] is False
        assert mocked_convert.call_args.kwargs["manual_verification"] is True

    def test_batch_passes_tesseract_cmd_to_convert(self, tmp_path):
        batch = tmp_path / "urls.txt"
        batch.write_text("https://example.com\n", encoding="utf-8")

        with patch("url2pdf.cli.convert", return_value=tmp_path / "out.pdf") as mocked_convert:
            code = main([
                "--batch",
                str(batch),
                "--ocr",
                "--tesseract-cmd",
                "C:/Tesseract/tesseract.exe",
            ])

        assert code == 0
        assert mocked_convert.call_args.kwargs["tesseract_cmd"] == "C:/Tesseract/tesseract.exe"

    def test_keyboard_interrupt_returns_130(self):
        with patch("url2pdf.cli.convert", side_effect=KeyboardInterrupt):
            code = main(["https://example.com"])
        assert code == 130


class TestConvert:
    def test_headed_option_is_passed_to_chromium(self, tmp_path):
        out = tmp_path / "out.pdf"
        page = MagicMock()
        page.title.return_value = "Example"
        page.evaluate.return_value = True
        context_obj = MagicMock()
        context_obj.new_page.return_value = page
        browser = MagicMock()
        browser.new_context.return_value = context_obj
        playwright = MagicMock()
        playwright.chromium.launch.return_value = browser
        ctx = MagicMock()
        ctx.__enter__.return_value = playwright

        with (
            patch("url2pdf.converter.sync_playwright", return_value=ctx),
            patch("url2pdf.converter.time.sleep"),
        ):
            result = convert(
                "https://example.com",
                str(out),
                scroll_rounds=0,
                verbose=False,
                headless=False,
            )

        assert result == out.resolve()
        playwright.chromium.launch.assert_called_once_with(headless=False)
        page.goto.assert_called_once_with(
            "https://example.com", wait_until="domcontentloaded", timeout=60_000
        )


    def test_manual_verification_waits_when_challenge_detected(self):
        page = MagicMock()
        page.title.side_effect = ["Just a moment...", "Example"]

        with (
            patch("builtins.input", return_value=""),
            patch("url2pdf.converter.time.sleep"),
        ):
            wait_for_manual_verification(page, timeout=1, verbose=False)

        page.wait_for_load_state.assert_called_once_with("load", timeout=1_000)

    def test_print_prep_does_not_absolute_position_fixed_elements(self):
        assert "position = 'absolute'" not in _JS_PREPARE_FOR_PRINT
        assert "position = 'static'" in _JS_PREPARE_FOR_PRINT
        assert "transform = 'none'" in _JS_PREPARE_FOR_PRINT
        assert "margin-left: 0" in _PRINT_CSS
        assert "main, div, section, article" in _PRINT_CSS
        assert "break-inside: auto" in _PRINT_CSS
        assert _PRINT_CSS.count("height: auto !important;") == 1
        assert "el.scrollTop = 0" in _JS_PREPARE_FOR_PRINT
        assert "keepOverflow" in _JS_PREPARE_FOR_PRINT
        assert "swiper" in _JS_PREPARE_FOR_PRINT
        assert 'img[src*="ads.jobkorea"]' in _JS_DISMISS_OVERLAYS
        assert "gamejob" in _JS_LINEARIZE_RECRUIT_PAGE
        assert "paddingLeft = '8mm'" in _JS_LINEARIZE_RECRUIT_PAGE
        assert ".view__content" in _JS_LINEARIZE_RECRUIT_PAGE
        assert ".section-view-detail *" in _JS_LINEARIZE_RECRUIT_PAGE
        assert ".content-right" in _JS_LINEARIZE_RECRUIT_PAGE
        assert ".content-left *" in _JS_LINEARIZE_RECRUIT_PAGE
        assert "cssText += ';' +" in _JS_LINEARIZE_RECRUIT_PAGE

    def test_normalize_ocr_text_joins_korean_characters(self):
        assert _normalize_ocr_text("새 로 운 버 터") == "새로운버터"
        assert _normalize_ocr_text("Unity 프 로 그 래 머") == "Unity 프로그래머"

    def test_find_ocr_fontfile_returns_first_existing_candidate(self):
        existing = _OCR_FONT_CANDIDATES[1]
        with patch("url2pdf.converter.Path.is_file", side_effect=[False, True]):
            assert _find_ocr_fontfile() == existing

    def test_ocr_text_runs_join_near_korean_tokens_only(self):
        data = {
            "text": ["새", "로", "운", "버", "터"],
            "left": [0, 8, 16, 40, 48],
            "width": [7, 7, 7, 7, 7],
            "height": [10, 10, 10, 10, 10],
        }

        assert _ocr_text_runs(data, [0, 1, 2, 3, 4]) == [[0, 1, 2], [3, 4]]


class TestGui:
    def test_gui_passes_new_options_to_convert(self, tmp_path):
        app = object.__new__(Url2PdfApp)
        app.root = MagicMock()
        app.root.after.side_effect = lambda _ms, callback, *args: callback(*args)
        app._on_success = MagicMock()
        app._on_error = MagicMock()

        out = tmp_path / "out.pdf"
        recipe = tmp_path / "recipe.json"
        recipe.write_text('[{"action":"wait","ms":1}]', encoding="utf-8")

        with patch("url2pdf.gui.convert", return_value=out) as mocked_convert:
            app._run_convert(
                "https://example.com",
                str(out),
                False,
                "evidence",
                True,
                str(recipe),
                True,
                "C:/Tesseract/tesseract.exe",
                "kor+eng",
                "single",
                "ko",
            )

        assert mocked_convert.call_args.kwargs == {
            "url": "https://example.com",
            "output": str(out),
            "headless": False,
            "profile": "evidence",
            "preview": True,
            "recipe": str(recipe),
            "ocr": True,
            "ocr_lang": "kor+eng",
            "tesseract_cmd": "C:/Tesseract/tesseract.exe",
            "pdf_layout": "single",
            "lang": "ko",
        }
        app._on_success.assert_called_once_with(out)
        app._on_error.assert_not_called()

    def test_gui_accepts_tesseract_path_when_not_on_path(self):
        app = object.__new__(Url2PdfApp)
        app._ = lambda key, **_kwargs: key
        app.url_var = MagicMock()
        app.url_var.get.return_value = "https://example.com"
        app.ocr_var = MagicMock()
        app.ocr_var.get.return_value = True
        app.tess_cmd_var = MagicMock()
        app.tess_cmd_var.get.return_value = "C:/Program Files/Tesseract-OCR/tesseract.exe"
        app.convert_btn = MagicMock()
        app.status_var = MagicMock()
        app.headed_var = MagicMock()
        app.headed_var.get.return_value = False
        app.profile_var = MagicMock()
        app.profile_var.get.return_value = "faithful"
        app.preview_var = MagicMock()
        app.preview_var.get.return_value = False
        app.recipe_var = MagicMock()
        app.recipe_var.get.return_value = ""
        app.output_var = MagicMock()
        app.output_var.get.return_value = "out.pdf"
        app.lang_var = MagicMock()
        app.lang_var.get.return_value = "ko"
        app.pdf_layout_var = MagicMock()
        app.pdf_layout_var.get.return_value = "pages"
        app.ocr_lang_var = MagicMock()
        app.ocr_lang_var.get.return_value = "eng"

        with (
            patch.dict("sys.modules", {"pytesseract": MagicMock()}),
            patch("url2pdf.gui.shutil.which", return_value=None),
            patch("url2pdf.gui.messagebox.showerror") as showerror,
            patch("url2pdf.gui.messagebox.showwarning") as showwarning,
            patch("url2pdf.gui.threading.Thread") as thread,
        ):
            app.start_conversion()

        thread.assert_called_once()
        showerror.assert_not_called()
        showwarning.assert_not_called()


class TestVersion:
    def test_semver_format(self):
        assert re.match(r"^\d+\.\d+\.\d+", __version__)
