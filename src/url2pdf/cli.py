"""url2pdf - command-line interface."""

from __future__ import annotations

import argparse
import sys

from .converter import convert
from .exceptions import Url2PdfError
from .i18n import get_translator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="url2pdf",
        description="Convert any web page to a searchable PDF.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  url2pdf https://example.com
  url2pdf https://example.com -o report.pdf
  url2pdf https://example.com --format Letter --scale 0.85 --timeout 90
  url2pdf https://example.com --headed --manual-verification
  url2pdf https://example.com -q          # suppress progress output
""",
    )
    parser.add_argument("url", nargs="?", help="URL of the page to convert")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check HTTP connection only, do not generate PDF",
    )
    parser.add_argument(
        "--batch",
        metavar="FILE",
        help="Process multiple URLs from a text file",
    )
    parser.add_argument(
        "--session",
        metavar="FILE",
        help="Path to Playwright storageState.json for login sessions",
    )
    parser.add_argument(
        "--profile",
        choices=["faithful", "evidence", "reading"],
        default="faithful",
        help="Capture profile (faithful: default, evidence: metadata hash, reading: removes ads)",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Preview the PDF using the OS default viewer after generation",
    )
    parser.add_argument(
        "--recipe",
        help="Path to a JSON recipe file to execute custom actions before capture",
    )
    parser.add_argument(
        "--ocr",
        action="store_true",
        help="Use Tesseract OCR to generate PDF from full-page screenshot",
    )
    parser.add_argument(
        "--ocr-lang",
        default="eng",
        help="Language passed to Tesseract (e.g., 'eng', 'kor+eng') (default: eng)",
    )
    parser.add_argument(
        "--lang",
        choices=["auto", "ko", "en"],
        default="auto",
        help="Language for CLI messages (default: auto)",
    )
    parser.add_argument(
        "-o", "--output",
        metavar="FILE",
        help="output PDF path (default: auto-generated from page title)",
    )
    parser.add_argument(
        "--format",
        default="A4",
        metavar="FORMAT",
        help="paper format: A4, Letter, A3, etc. (default: A4)",
    )
    parser.add_argument(
        "--scale",
        type=float,
        default=0.9,
        metavar="SCALE",
        help="CSS scale factor 0.1-2.0 (default: 0.9)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        metavar="SECONDS",
        help="page load timeout in seconds (default: 60)",
    )
    parser.add_argument(
        "--scroll-rounds",
        type=int,
        default=80,
        metavar="N",
        dest="scroll_rounds",
        help="max scroll iterations for lazy content (default: 80)",
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        help="show the Chromium browser window instead of running headless",
    )
    parser.add_argument(
        "--manual-verification",
        action="store_true",
        help="pause when browser verification is detected so it can be completed manually",
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="suppress progress messages",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    _ = get_translator(args.lang)

    if not args.url and not args.batch:
        parser.error("either url or --batch must be provided")

    if not 0.1 <= args.scale <= 2.0:
        parser.error("--scale must be between 0.1 and 2.0")

    try:
        if args.batch:
            try:
                with open(args.batch, encoding="utf-8") as f:
                    lines = [
                        line.strip() for line in f 
                        if line.strip() and not line.strip().startswith("#")
                    ]
            except OSError as exc:
                parser.error(f"Failed to read batch file: {exc}")
            
            for line in lines:
                try:
                    if not args.quiet:
                        print(f"\nProcessing batch item: {line}")
                    convert(
                        url=line,
                        output=None,
                        timeout=args.timeout,
                        scroll_rounds=args.scroll_rounds,
                        page_format=args.format,
                        scale=args.scale,
                        verbose=not args.quiet,
                        headless=not args.headed,
                        manual_verification=args.manual_verification,
                        check_only=args.check,
                        session_file=args.session,
                        profile=args.profile,
                        preview=args.preview,
                        recipe=args.recipe,
                        ocr=args.ocr,
                        ocr_lang=args.ocr_lang,
                        lang=args.lang,
                    )
                except Url2PdfError as exc:
                    print(f"Error processing {line}: {exc}", file=sys.stderr)
            return 0
        else:
            convert(
                url=args.url,
                output=args.output,
                timeout=args.timeout,
                scroll_rounds=args.scroll_rounds,
                page_format=args.format,
                scale=args.scale,
                verbose=not args.quiet,
                headless=not args.headed,
                manual_verification=args.manual_verification,
                check_only=args.check,
                session_file=args.session,
                profile=args.profile,
                preview=args.preview,
                recipe=args.recipe,
                ocr=args.ocr,
                ocr_lang=args.ocr_lang,
                lang=args.lang,
            )
            return 0
    except Url2PdfError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nAborted.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
