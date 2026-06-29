"""
Core PDF conversion logic using Playwright.
"""

from __future__ import annotations

import re
import time
from datetime import datetime
from pathlib import Path

from playwright.sync_api import Page, sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from .exceptions import PageLoadError, PDFGenerationError

CHALLENGE_TITLE_KEYWORDS = (
    "just a moment",
    "checking your browser",
    "verify you are human",
    "attention required",
)

_PRINT_CSS = """
* {
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
    color-adjust: exact !important;
    box-sizing: border-box;
}
html, body {
    height: auto !important;
    overflow: visible !important;
    background: #fff !important;
}
body {
    font-family:
        'Malgun Gothic', 'Noto Sans KR', 'Noto Sans CJK KR',
        'Apple SD Gothic Neo', 'Nanum Gothic',
        'Hiragino Sans', 'Yu Gothic', 'MS Gothic',
        'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei',
        -apple-system, BlinkMacSystemFont, 'Segoe UI',
        'Helvetica Neue', Arial, sans-serif !important;
}
img, svg, figure, table, pre, code, blockquote,
section, article, .card, [class*="card"], [class*="block"] {
    page-break-inside: avoid !important;
    break-inside: avoid !important;
    max-width: 100% !important;
    height: auto !important;
}
h1, h2, h3, h4, h5, h6 {
    page-break-after: avoid !important;
    break-after: avoid !important;
}
p, li {
    orphans: 3 !important;
    widows: 3 !important;
}
video, audio, iframe[src*="youtube"], iframe[src*="ads"],
canvas:not([class*="chart"]):not([class*="graph"]) {
    display: none !important;
}
"""

_JS_DISMISS_OVERLAYS = """
() => {
    const HIGH_Z = 100;
    const VIEW_AREA = window.innerWidth * window.innerHeight;

    const selectors = [
        '[id*="cookie"]', '[class*="cookie"]',
        '[id*="gdpr"]',  '[class*="gdpr"]',
        '[id*="consent"]', '[class*="consent"]',
        '[id*="popup"]',  '[class*="popup"]',
        '[id*="modal"]',  '[class*="modal"]',
        '[id*="overlay"]', '[class*="overlay"]',
        '[id*="banner"]',  '[class*="banner"]',
        '[id*="paywall"]', '[class*="paywall"]',
        '[id*="subscribe"]', '[class*="subscribe"]',
        '[id*="newsletter"]', '[class*="newsletter"]',
        '[role="dialog"]', '[role="alertdialog"]',
        '[aria-modal="true"]',
        '#onetrust-banner-sdk', '#onetrust-pc-sdk',
        '.cc-banner', '.cc-window',
        '#didomi-popup', '#didomi-host',
        '.fc-consent-root', '.sp-message-container',
        '#qc-cmp2-ui', '#qc-cmp2-container',
        '[id*="CybotCookiebotDialog"]',
        '[class*="CookieBanner"]', '[class*="PrivacyAlert"]',
        '[id*="privacy-policy-banner"]',
    ];

    let removed = 0;
    for (const sel of selectors) {
        try {
            for (const el of document.querySelectorAll(sel)) {
                const s = getComputedStyle(el);
                const zIdx = parseInt(s.zIndex) || 0;
                const rect = el.getBoundingClientRect();
                const area = rect.width * rect.height;
                if (
                    (s.position === 'fixed' || s.position === 'sticky' || zIdx > HIGH_Z)
                    && area > VIEW_AREA * 0.03
                ) {
                    el.remove();
                    removed++;
                }
            }
        } catch (_) {}
    }

    if (getComputedStyle(document.body).overflow === 'hidden') {
        document.body.style.overflow = 'auto';
    }
    if (getComputedStyle(document.documentElement).overflow === 'hidden') {
        document.documentElement.style.overflow = 'auto';
    }

    return removed;
}
"""

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

_JS_PREPARE_FOR_PRINT = """
() => {
    document.documentElement.style.cssText +=
        ';height:auto!important;overflow:visible!important;';
    document.body.style.cssText +=
        ';height:auto!important;overflow:visible!important;max-width:none!important;';

    for (const el of document.querySelectorAll('*')) {
        try {
            const s = getComputedStyle(el);
            if (s.position === 'fixed' || s.position === 'sticky') {
                el.style.position = 'static';
            }
            if (
                ['hidden', 'auto', 'scroll'].includes(s.overflow) ||
                ['auto', 'scroll'].includes(s.overflowY)
            ) {
                if (el.scrollHeight > 200) {
                    el.style.overflow = 'visible';
                    el.style.maxHeight = 'none';
                    el.style.height = 'auto';
                }
            }
        } catch (_) {}
    }

    window.scrollTo(0, 0);
    return true;
}
"""

_JS_WAIT_IMAGES = """
() => {
    const imgs = Array.from(document.querySelectorAll('img[src]'));
    if (imgs.length === 0) return Promise.resolve(true);
    return Promise.all(
        imgs.map(img => {
            if (img.complete && img.naturalWidth > 0) return Promise.resolve();
            return new Promise(resolve => {
                img.onload = resolve;
                img.onerror = resolve;
                setTimeout(resolve, 4000);
            });
        })
    ).then(() => true);
}
"""


def make_filename(title: str) -> str:
    safe = re.sub(r'[\\/:*?"<>|]', "_", title).strip() or "page"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{safe[:60]}_{stamp}.pdf"


def is_challenge_page(
    title: str,
    challenge_title_keywords: tuple[str, ...] | None = None,
) -> bool:
    keywords = challenge_title_keywords or CHALLENGE_TITLE_KEYWORDS
    normalized = title.casefold()
    return any(keyword in normalized for keyword in keywords)


def wait_for_manual_verification(
    page: Page,
    *,
    timeout: int = 60,
    challenge_title_keywords: tuple[str, ...] | None = None,
    verbose: bool = True,
) -> None:
    if not is_challenge_page(page.title(), challenge_title_keywords):
        return

    if verbose:
        print()
        print("[manual] Browser verification page detected.")
        print("[manual] Complete the verification in the opened Chromium window.")
    input("[manual] After the real page loads, press Enter here to continue...")
    page.wait_for_load_state("load", timeout=timeout * 1_000)
    time.sleep(1.5)

    if is_challenge_page(page.title(), challenge_title_keywords):
        raise PageLoadError("Still on a browser verification page. PDF creation was stopped.")


def convert(
    url: str,
    output: str | None = None,
    *,
    timeout: int = 60,
    scroll_rounds: int = 80,
    scroll_pause: float = 0.8,
    page_format: str = "A4",
    scale: float = 0.9,
    verbose: bool = True,
    headless: bool = True,
    manual_verification: bool = False,
    challenge_title_keywords: tuple[str, ...] | None = None,
    screenshot_path: str | None = None,
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
        CSS scale applied when rendering (0.1 to 2.0).
    verbose:
        Print progress messages to stdout when *True*.
    headless:
        Launch Chromium without a visible browser window when *True*.
    manual_verification:
        Pause for browser verification when a challenge page is detected.
    challenge_title_keywords:
        Optional page title keywords used to detect browser verification pages.

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
        browser = p.chromium.launch(
            headless=headless,
        )
        try:
            context = browser.new_context(
                viewport={"width": 1280, "height": 900},
                locale="ko-KR",
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0.0.0 Safari/537.36"
                ),
                extra_http_headers={
                    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
                              "image/avif,image/webp,*/*;q=0.8",
                },
            )
            context.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            page = context.new_page()

            log(f"[1/6] Loading: {url}")
            try:
                page.goto(url, wait_until="load", timeout=timeout * 1_000)
            except PlaywrightTimeoutError as exc:
                raise PageLoadError(
                    f"Page did not load within {timeout}s: {url}"
                ) from exc
            except Exception as exc:
                raise PageLoadError(f"Failed to open URL '{url}': {exc}") from exc

            time.sleep(2.0)

            if manual_verification:
                wait_for_manual_verification(
                    page,
                    timeout=timeout,
                    challenge_title_keywords=challenge_title_keywords,
                    verbose=verbose,
                )

            log("[2/6] Dismissing overlays / popups...")
            try:
                dismissed = page.evaluate(_JS_DISMISS_OVERLAYS)
                if verbose and dismissed:
                    print(f"  [info] Removed {dismissed} overlay element(s).")
            except Exception:
                dismissed = 0
            time.sleep(0.5)
            try:
                page.wait_for_load_state("load", timeout=5_000)
            except Exception:
                pass
            time.sleep(0.5)

            log("[3/6] Scrolling to load lazy content...")
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

            log("[4/6] Waiting for images...")
            try:
                page.evaluate(_JS_WAIT_IMAGES)
            except Exception:
                pass
            time.sleep(0.5)

            title = page.title() or "page"

            log("[5/6] Injecting print CSS and preparing DOM...")
            try:
                page.add_style_tag(content=_PRINT_CSS)
            except Exception:
                pass
            page.evaluate(_JS_PREPARE_FOR_PRINT)
            time.sleep(0.8)

            dest = Path(output) if output else Path(make_filename(title))

            log(f"[6/6] Generating PDF: {dest}")
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
            except Exception:
                log("  [warn] PDF generation failed, retrying with minimal DOM...")
                try:
                    page.evaluate(
                        "() => { "
                        "const els = document.querySelectorAll('script,style,noscript,iframe');"
                        "els.forEach(e => e.remove()); "
                        "document.documentElement.style.cssText = 'height:auto;overflow:visible;'; "
                        "document.body.style.cssText = 'height:auto;overflow:visible;margin:0;'; "
                        "}"
                    )
                    time.sleep(1.0)
                    page.pdf(
                        path=str(dest),
                        format=page_format,
                        print_background=False,
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

            if screenshot_path:
                try:
                    page.screenshot(path=screenshot_path, full_page=False)
                except Exception:
                    pass

            log(f"Done: {dest.resolve()}")
            return dest.resolve()

        finally:
            browser.close()
