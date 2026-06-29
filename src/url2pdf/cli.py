"""url2pdf - command-line interface."""

from __future__ import annotations

import argparse
import sys

from .converter import convert
from .exceptions import Url2PdfError


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
    parser.add_argument("url", help="URL of the page to convert")
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

    if not 0.1 <= args.scale <= 2.0:
        parser.error("--scale must be between 0.1 and 2.0")

    try:
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
