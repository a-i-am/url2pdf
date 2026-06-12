# -*- coding: utf-8 -*-
"""
Core PDF conversion logic using Playwright.
"""

from __future__ import annotations

import re
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from .exceptions import PageLoadError, PDFGenerationError


# ---------------------------------------------------------------------------
# JavaScript helpers injected into the page
# ---------------------------------------------------------------------------

_JS_FIND_SCROLLER = """
() => {
    let best = document.scrollingElement || document.body;
    let bestDiff = best.scrollHeight - best.clientHeight;
    for (const el of document.querySelectorAll('*')) {
        const diff = el.scrollHeight - el.clientHeight;
        if (diff > bestDiff && el.clientHeight > 200) {
            best = el;
            bestDiff = diff;
        }
    }
    best.setAttribute('data-pdf-scroller', '1');
}
"""

_JS_REBUILD_FOR_PRINT = """
() => {
    const scroller = document.querySelector('[data-pdf-scroller]');
    if (!scroller) return false;
    const content = scroller.cloneNode(true);
    content.removeAttribute('data-pdf-scroller');
    document.body.replaceChildren(content);

    document.documentElement.style.cssText = 'height:auto;overflow:visible;';
    document.body.style.cssText =
        'height:auto;overflow:visible;margin:0 auto;max-width:900px;background:#fff;';
    content.style.height = 'auto';
    content.style.maxHeight = 'none';
    content.style.overflow = 'visible';

    for (const el of content.querySelectorAll('*')) {
        const s = getComputedStyle(el);
        if (['hidden','auto','scroll'].includes(s.overflow) ||
            ['auto','scroll'].includes(s.overflowY)) {
            el.style.overflow = 'visible';
            el.style.maxHeight = 'none';
        }
        if (s.position === 'fixed' || s.position === 'sticky') {
            el.style.position = 'static';
        }
    }
    window.scrollTo(0, 0);
    return true;
}
"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def make_filename(title: str) -> str:
    """Return a safe, timestamped filename derived from *title*."""
    safe = re.sub(r'[\\/:*?"<>|]', "_", title).strip() or "page"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{safe[:60]}_{stamp}.pdf"


def convert(
    url: str,
    output: Optional[str] = None,
    *,
    timeout: int = 60,
    scroll_rounds: int = 80,
    scroll_pause: float = 0.8,
    page_format: str = "A4",
    scale: float = 0.9,
    verbose: bool = True,
) -> Path:
    """Convert *url* to a searchable PDF and return its :class:`~pathlib.Path`.

    Parameters
    ----------
    url:
        The web page URL to convert.
    output:
        Destination file path.  Auto-generated from the page title when omitted.
    timeout:
        Navigation timeout in seconds (default 60).
    scroll_rounds:
        Maximum number of scroll iterations used to trigger lazy-loaded content.
    scroll_pause:
        Seconds to wait between scroll steps.
    page_format:
        PDF paper format passed to Playwright (e.g. ``"A4"``, ``"Letter"``).
    scale:
        CSS scale applied when rendering (0.1 – 2.0).
    verbose:
        Print progress messages to stdout when *True*.

    Returns
    -------
    Path
        Absolute path of the generated PDF.

    Raises
    ------
    PageLoadError
        When the page cannot be reached or times out.
    PDFGenerationError
        When Playwright fails to write the PDF.
    """

    def log(msg: str) -> None:
        if verbose:
            print(msg)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={"width": 1280, "height": 1600})

            # ── 1. Load page ────────────────────────────────────────────────
            log(f"[1/5] Loading: {url}")
            try:
                page.goto(url, wait_until="load", timeout=timeout * 1_000)
            except PlaywrightTimeoutError as exc:
                raise PageLoadError(
                    f"Page did not load within {timeout}s: {url}"
                ) from exc
            except Exception as exc:
                raise PageLoadError(f"Failed to open URL '{url}': {exc}") from exc

            time.sleep(1.5)

            # ── 2. Scroll to trigger lazy content ───────────────────────────
            log("[2/5] Scrolling to load lazy content...")
            page.evaluate(_JS_FIND_SCROLLER)
            last_height = -1
            for _ in range(scroll_rounds):
                try:
                    height = page.evaluate(
                        "() => {"
                        "  const el = document.querySelector('[data-pdf-scroller]');"
                        "  if (!el) return -1;"
                        "  el.scrollTop = el.scrollHeight;"
                        "  return el.scrollHeight;"
                        "}"
                    )
                except Exception:
                    break
                time.sleep(scroll_pause)
                if height == last_height:
                    break
                last_height = height

            title = page.title() or "page"

            # ── 3. Rebuild DOM for print ─────────────────────────────────────
            log("[3/5] Rebuilding DOM for print...")
            ok = page.evaluate(_JS_REBUILD_FOR_PRINT)
            if not ok:
                log("  [warn] No scroll container found — using full page.")
            time.sleep(0.8)

            # ── 4. Resolve output path ───────────────────────────────────────
            dest = Path(output) if output else Path(make_filename(title))

            # ── 5. Generate PDF ──────────────────────────────────────────────
            log(f"[4/5] Generating PDF: {dest}")
            page.emulate_media(media="screen")
            try:
                page.pdf(
                    path=str(dest),
                    format=page_format,
                    print_background=True,
                    margin={
                        "top": "12mm",
                        "bottom": "12mm",
                        "left": "12mm",
                        "right": "12mm",
                    },
                    scale=scale,
                )
            except Exception as exc:
                raise PDFGenerationError(f"Failed to write PDF: {exc}") from exc

            log(f"[5/5] Done → {dest.resolve()}")
            return dest.resolve()

        finally:
            browser.close()
