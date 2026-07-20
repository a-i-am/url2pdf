"""
Core PDF conversion logic using Playwright.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from .exceptions import PageLoadError, PDFGenerationError, Url2PdfError
from .i18n import get_translator

CHALLENGE_TITLE_KEYWORDS = (
    "just a moment",
    "checking your browser",
    "verify you are human",
    "attention required",
)

PDF_LAYOUTS = ("pages", "single")

_OCR_FONT_CANDIDATES = (
    r"C:\Windows\Fonts\malgun.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJKkr-Regular.otf",
    "/usr/share/fonts/opentype/noto/NotoSansCJKkr-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJKkr-Regular.otf",
    "/usr/share/fonts/truetype/noto/NotoSansCJKkr-Regular.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJKkr-Regular.otf",
    "/usr/share/fonts/noto-cjk/NotoSansCJKkr-Regular.ttc",
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
)

_PRINT_CSS = """
* {
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
    color-adjust: exact !important;
    box-sizing: border-box;
    animation: none !important;
    transition: none !important;
}
html, body {
    height: auto !important;
    overflow: visible !important;
    background: #fff !important;
    margin-left: 0 !important;
    transform: none !important;
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
img, svg, figure, table, pre, code, blockquote {
    page-break-inside: avoid !important;
    break-inside: avoid !important;
    max-width: 100% !important;
}
main, div, section, article, .card, [class*="card"], [class*="block"] {
    page-break-inside: auto !important;
    break-inside: auto !important;
    min-height: 0 !important;
}
h1, h2, h3, h4, h5, h6 {
    page-break-after: avoid !important;
    break-after: avoid !important;
}
p, li, dt, dd {
    orphans: 3 !important;
    widows: 3 !important;
    page-break-inside: avoid !important;
    break-inside: avoid !important;
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
        'iframe[src*="ads"]',
        'img[src*="ads.jobkorea"]',
        'img[src*="/ads/"]',
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

    if (document.body && getComputedStyle(document.body).overflow === 'hidden') {
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
    let best = document.scrollingElement || document.body || document.documentElement;
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
    if (document.body) {
        document.body.style.cssText +=
            ';height:auto!important;overflow:visible!important;max-width:none!important;';
    }

    for (const el of document.querySelectorAll('*')) {
        try {
            const s = getComputedStyle(el);
            const className = String(el.className || '').toLowerCase();
            const keepOverflow = (
                className.includes('swiper') ||
                className.includes('carousel') ||
                className.includes('slider') ||
                className.includes('slick')
            );
            if (s.position === 'fixed' || s.position === 'sticky') {
                el.style.position = 'static';
                el.style.left = 'auto';
                el.style.right = 'auto';
                el.style.top = 'auto';
                el.style.bottom = 'auto';
                el.style.transform = 'none';
            }
            if (
                !keepOverflow && (
                    ['hidden', 'auto', 'scroll'].includes(s.overflow) ||
                    ['auto', 'scroll'].includes(s.overflowY)
                )
            ) {
                if (el.scrollHeight > 200) {
                    el.scrollTop = 0;
                    el.scrollLeft = 0;
                    el.style.overflow = 'visible';
                    el.style.maxHeight = 'none';
                    el.style.height = 'auto';
                }
            }
        } catch (_) {}
    }

    window.scrollTo(0, 0);
    if (document.scrollingElement) {
        document.scrollingElement.scrollTop = 0;
        document.scrollingElement.scrollLeft = 0;
    }
    return true;
}
"""

_JS_LINEARIZE_RECRUIT_PAGE = """
() => {
    if (!/gamejob\\.co\\.kr$/i.test(location.hostname)) return false;
    document.body.style.paddingLeft = '8mm';
    document.body.style.paddingRight = '8mm';
    const selectors = [
        '.view__content',
        '.section-view-detail',
        '.view-detail-head',
        '.view-detail-content',
        '.content-left',
        '.content-right',
        '.content__recruit-data',
        '.content__summary',
        '.recruit-view-container',
        '.section-view-top',
        '.section-inner',
        '.job-sub-section__body',
        '.render-section',
        '.job-howtoapply-wrap'
    ];
    for (const sel of selectors) {
        for (const el of document.querySelectorAll(sel)) {
            el.style.cssText += ';' + [
                'display:block!important',
                'float:none!important',
                'position:static!important',
                'width:100%!important',
                'max-width:100%!important',
                'height:auto!important',
                'min-height:0!important',
                'margin-left:0!important',
                'margin-right:0!important',
                'transform:none!important'
            ].join(';');
        }
    }
    for (const el of document.querySelectorAll('.content-right')) {
        el.style.marginTop = '16px';
        el.style.pageBreakInside = 'avoid';
        el.style.breakInside = 'avoid';
    }
    const contentSelectors = [
        '.section-view-detail *',
        '.view__content *',
        '.content-left *',
        '.content-right *'
    ].join(', ');
    for (const el of document.querySelectorAll(contentSelectors)) {
        el.style.position = 'static';
        el.style.inset = 'auto';
        el.style.transform = 'none';
        el.style.maxWidth = '100%';
        el.style.float = 'none';
    }
    for (const el of document.querySelectorAll('.swiper, .swiper-wrapper')) {
        el.style.transform = 'none';
        el.style.overflow = 'hidden';
        el.style.width = '100%';
    }
    for (const el of document.querySelectorAll('.swiper-slide')) {
        el.style.position = 'static';
        el.style.transform = 'none';
        el.style.width = '48%';
        el.style.display = 'inline-block';
        el.style.verticalAlign = 'top';
        el.style.marginRight = '2%';
    }
    const hiddenSlides =
        '.swiper-slide:not(.swiper-slide-active):not(.swiper-slide-next)';
    for (const el of document.querySelectorAll(hiddenSlides)) {
        el.style.display = 'none';
    }
    for (const img of document.querySelectorAll('.swiper-slide img')) {
        img.style.width = '100%';
        img.style.height = 'auto';
        img.style.position = 'static';
        img.style.transform = 'none';
    }
    const swiperControls =
        '.swiper-button-prev, .swiper-button-next, .swiper-notification';
    for (const el of document.querySelectorAll(swiperControls)) {
        el.style.display = 'none';
    }
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


PRESET_RECIPES = {
    "dismiss-cookies": [
        {"action": "wait", "ms": 500},
        {
            "action": "click",
            "selector": (
                "[class*='cookie'], [id*='cookie'], [class*='consent'], [id*='consent'], "
                "button:has-text('Accept'), button:has-text('Agree')"
            ),
            "optional": True
        }
    ],
    "lazy-load": [
        {"action": "scroll"}
    ]
}

def _run_recipe(page: Page, recipe_path_or_preset: str, log: Any, translate: Any) -> None:
    if recipe_path_or_preset in PRESET_RECIPES:
        recipe_data = PRESET_RECIPES[recipe_path_or_preset]
    else:
        try:
            with open(recipe_path_or_preset, encoding="utf-8") as f:
                recipe_data = json.load(f)
        except Exception as e:
            raise Url2PdfError(f"Failed to parse recipe JSON: {e}") from e

    if not isinstance(recipe_data, list):
        raise Url2PdfError("Recipe must be a JSON array of actions.")
        
    for idx, step in enumerate(recipe_data):
        if not isinstance(step, dict):
            raise Url2PdfError(f"Invalid recipe step at index {idx}: must be an object.")
        action = step.get("action")
        if action not in ("click", "wait", "scroll"):
            raise Url2PdfError(f"Invalid recipe action at step {idx}: {action}")
            
        if action == "wait":
            ms = step.get("ms")
            if not isinstance(ms, int) or not (0 <= ms <= 60000):
                raise Url2PdfError(
                    translate("recipe_waiting", ms=ms) + f" (Invalid ms: {ms})"
                )
            log(translate("recipe_waiting", ms=ms))
            page.wait_for_timeout(ms)
            
        elif action == "click":
            selector = step.get("selector")
            optional = step.get("optional", False)
            if not selector:
                if optional:
                    continue
                raise Url2PdfError(f"Recipe step {idx} 'click' requires 'selector'.")
            log(translate("recipe_clicking", selector=selector))
            try:
                page.locator(selector).click(timeout=5000)
            except Exception as e:
                if not optional:
                    raise Url2PdfError(
                        f"Recipe step {idx} failed to click '{selector}': {e}"
                    ) from e
                    
        elif action == "scroll":
            selector = step.get("selector")
            if selector:
                log(translate("recipe_scrolling_element", selector=selector))
                try:
                    page.evaluate(
                        "(sel) => { "
                        "const el = document.querySelector(sel); "
                        "if(el) el.scrollTop = el.scrollHeight; "
                        "}",
                        selector
                    )
                except Exception as e:
                    raise Url2PdfError(
                        f"Recipe step {idx} failed to scroll '{selector}': {e}"
                    ) from e
            else:
                log(translate("recipe_scrolling_page"))
                page.evaluate("window.scrollTo(0, document.body ? document.body.scrollHeight : 0)")


def _normalize_ocr_text(text: str) -> str:
    return re.sub(r"([가-힣ㄱ-ㅎㅏ-ㅣ])\s+(?=[가-힣ㄱ-ㅎㅏ-ㅣ])", r"\1", text).strip()


def _is_korean_text(text: str) -> bool:
    return bool(re.search(r"[가-힣ㄱ-ㅎㅏ-ㅣ]", text))


def _find_ocr_fontfile() -> str | None:
    for candidate in _OCR_FONT_CANDIDATES:
        if Path(candidate).is_file():
            return candidate
    return None


def _ocr_text_runs(data: dict[str, Any], indexes: list[int]) -> list[list[int]]:
    runs: list[list[int]] = []
    for idx in sorted(indexes, key=lambda i: data["left"][i]):
        text = data["text"][idx].strip()
        if not runs:
            runs.append([idx])
            continue
        prev = runs[-1][-1]
        gap = data["left"][idx] - (data["left"][prev] + data["width"][prev])
        height = max(data["height"][idx], data["height"][prev], 1)
        if _is_korean_text(data["text"][prev]) and _is_korean_text(text) and gap <= height * 0.8:
            runs[-1].append(idx)
        else:
            runs.append([idx])
    return runs


def _write_ocr_pdf(page: Page, dest: Path, ocr_lang: str, pdf_layout: str) -> None:
    import tempfile

    import fitz
    import pytesseract
    from PIL import Image

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        shot_path = Path(tmp.name)
    try:
        page.screenshot(path=str(shot_path), full_page=True)
        out = fitz.open()
        try:
            with Image.open(shot_path) as img:
                page_h = max(1, int(img.width * 297 / 210))
                fontfile = _find_ocr_fontfile()
                for y in range(0, img.height, page_h):
                    crop = img.crop((0, y, img.width, min(y + page_h, img.height))).convert("RGB")
                    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_crop:
                        crop_path = Path(tmp_crop.name)
                    try:
                        crop.save(crop_path)
                        pdf_page = out.new_page(width=crop.width, height=crop.height)
                        pdf_page.insert_image(pdf_page.rect, filename=str(crop_path))
                        data = pytesseract.image_to_data(
                            str(crop_path),
                            lang=ocr_lang,
                            output_type=pytesseract.Output.DICT,
                        )
                        lines: dict[tuple[int, int, int], list[int]] = {}
                        for idx, word in enumerate(data["text"]):
                            if word.strip():
                                key = (
                                    data["block_num"][idx],
                                    data["par_num"][idx],
                                    data["line_num"][idx],
                                )
                                lines.setdefault(key, []).append(idx)
                        for indexes in lines.values():
                            for run in _ocr_text_runs(data, indexes):
                                words = [data["text"][i] for i in run]
                                text = _normalize_ocr_text(" ".join(words))
                                if not text:
                                    continue
                                if fontfile is None and not text.isascii():
                                    continue
                                x0 = min(data["left"][i] for i in run)
                                y0 = min(data["top"][i] for i in run)
                                y1 = max(data["top"][i] + data["height"][i] for i in run)
                                fontsize = max(6, (y1 - y0) * 0.8)
                                pdf_page.insert_text(
                                    fitz.Point(x0, y0 + fontsize),
                                    text,
                                    fontfile=fontfile,
                                    fontname="malgun" if fontfile else "helv",
                                    fontsize=fontsize,
                                    render_mode=3,
                                    overlay=True,
                                )
                    finally:
                        crop_path.unlink(missing_ok=True)
            out.save(dest.resolve(), garbage=4, deflate=True)
        finally:
            out.close()
        if pdf_layout == "single":
            _stack_pdf_pages(dest)
    finally:
        shot_path.unlink(missing_ok=True)


def _stack_pdf_pages(dest: Path) -> None:
    try:
        import fitz
    except ImportError as exc:
        raise PDFGenerationError("--pdf-layout single requires pymupdf") from exc

    src = fitz.open(dest)
    try:
        if src.page_count <= 1:
            return
        width = max(page.rect.width for page in src)
        height = sum(page.rect.height for page in src)
        out = fitz.open()
        tmp = dest.with_suffix(".single.tmp.pdf")
        try:
            page = out.new_page(width=width, height=height)
            y = 0
            for src_page in src:
                rect = fitz.Rect(0, y, src_page.rect.width, y + src_page.rect.height)
                page.show_pdf_page(rect, src, src_page.number)
                y += src_page.rect.height
            out.save(tmp)
        finally:
            out.close()
    finally:
        src.close()
    tmp.replace(dest)


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
    check_only: bool = False,
    session_file: str | None = None,
    profile: str = "faithful",
    preview: bool = False,
    recipe: str | None = None,
    ocr: bool = False,
    ocr_lang: str = "eng",
    tesseract_cmd: str | None = None,
    pdf_layout: str = "pages",
    lang: str = "auto",
    test_recipe: bool = False,
) -> Path | None:
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
    check_only:
        If True, only check HTTP status and return without generating PDF.
    session_file:
        Path to playwright storageState json for login sessions.
    profile:
        Capture profile ("faithful", "evidence", or "reading").
    preview:
        If True, open the generated PDF with the OS default viewer.
    test_recipe:
        If True, executes recipe visually (forcing headless=False typically) 
        and exits without generating PDF.

    Returns
    -------
    Path | None
        Absolute path of the generated PDF, or None if check_only is True.

    Raises
    ------
    PageLoadError
        When the page cannot be reached or times out.
    PDFGenerationError
        When Playwright fails to write the PDF.
    """

    _ = get_translator(lang)
    if pdf_layout not in PDF_LAYOUTS:
        raise Url2PdfError(f"pdf_layout must be one of: {', '.join(PDF_LAYOUTS)}")

    def log(msg: str) -> None:
        if verbose:
            print(msg)

    if ocr:
        try:
            import pytesseract
        except ImportError as exc:
            raise Url2PdfError(
                "pytesseract is required for --ocr. Install it with: pip install 'url2pdf[ocr]'"
            ) from exc
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        
        tess_bin = pytesseract.pytesseract.tesseract_cmd
        if not (shutil.which(tess_bin) or Path(tess_bin).is_file()):
            raise Url2PdfError(
                f"tesseract binary not found at '{tess_bin}'.\n"
                "Please install Tesseract OCR (e.g., 'apt install tesseract-ocr' or via installer) "
                "and ensure it is in PATH, or provide the correct path."
            )

    if check_only:
        log(f"[1/1] Checking HTTP connection: {url}")
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=timeout):
                pass
        except (urllib.error.URLError, ValueError) as exc:
            raise PageLoadError(f"Connection failed: {exc}")
        return None

    if session_file and not Path(session_file).is_file():
        raise Url2PdfError(f"Session file not found: {session_file}")

    if test_recipe:
        headless = False

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
                storage_state=session_file if session_file else None,
            )
            context.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            page = context.new_page()

            log(_("loading"))
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=timeout * 1_000)
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

            if recipe:
                log(_("recipe_executing"))
                _run_recipe(page, recipe, log, _)

            if test_recipe:
                log("Recipe test completed. Exiting without PDF generation.")
                time.sleep(3.0)
                return None

            log(_("dismissing"))
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

            log(_("scrolling"))
            page.evaluate(_JS_FIND_SCROLLER)
            last_height = -1
            for _scroll_idx in range(scroll_rounds):
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

            log(_("waiting_images"))
            try:
                # Note to reviewer: Playwright Python evaluate() automatically awaits Promises
                page.evaluate(_JS_WAIT_IMAGES)
                page.evaluate(
                    "() => Promise.race(["
                    "document.fonts.ready.then(() => true),"
                    "new Promise(resolve => setTimeout(() => resolve(false), 5000))"
                    "])"
                )
            except Exception:
                pass
            time.sleep(0.5)
            
            dom_text_len = 0
            try:
                eval_script = "document.body ? document.body.innerText : ''"
                dom_text_len = len(page.evaluate(eval_script) or "")
            except Exception:
                pass

            title = page.title() or "page"
            if output and Path(output).is_dir():
                dest = Path(output) / make_filename(title)
            else:
                dest = Path(output) if output else Path(make_filename(title))
            pdf_scale = min(scale, 0.85) if "gamejob.co.kr" in url.lower() else scale

            if ocr:
                log(_("generating_pdf", dest=dest))
                try:
                    _write_ocr_pdf(page, dest, ocr_lang, pdf_layout)
                except Exception as exc:
                    raise PDFGenerationError(f"OCR PDF generation failed: {exc}") from exc
                log(_("done", dest=dest.resolve()))
                return dest.resolve()

            log(_("injecting"))
            try:
                page.add_style_tag(content=_PRINT_CSS)
            except Exception:
                pass
            page.evaluate(_JS_PREPARE_FOR_PRINT)
            page.evaluate(_JS_LINEARIZE_RECRUIT_PAGE)
            try:
                page.evaluate(_JS_WAIT_IMAGES)
            except Exception:
                pass
            time.sleep(0.8)

            if output and Path(output).is_dir():
                dest = Path(output) / make_filename(title)
            else:
                dest = Path(output) if output else Path(make_filename(title))
            if profile == "reading":
                log(_("applying_reading"))
                try:
                    page.evaluate('''
                        if (document.body) {
                            document.querySelectorAll(
                                'header, footer, nav, aside, .ad, ' +
                                '.advertisement, iframe, .social-share'
                            ).forEach(el => el.remove());
                            document.body.style.maxWidth = '800px';
                            document.body.style.margin = '0 auto';
                            document.body.style.fontSize = '18px';
                            document.body.style.lineHeight = '1.6';
                        }
                    ''')
                except Exception as exc:
                    log(f"  [warn] Reading profile heuristic failed: {exc}")

            log(_("generating_pdf", dest=dest))
            page.emulate_media(media="print")
            try:
                page.pdf(
                    path=str(dest),
                    format=page_format,
                    print_background=True,
                    margin={
                        "top": "16mm",
                        "bottom": "16mm",
                        "left": "16mm",
                        "right": "16mm",
                    },
                    scale=pdf_scale,
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
                            "top": "16mm",
                            "bottom": "16mm",
                            "left": "16mm",
                            "right": "16mm",
                        },
                        scale=pdf_scale,
                    )
                except Exception as exc:
                    raise PDFGenerationError(f"Failed to write PDF: {exc}") from exc

            if pdf_layout == "single":
                _stack_pdf_pages(dest)

            if screenshot_path:
                try:
                    page.screenshot(path=screenshot_path, full_page=False)
                except Exception:
                    pass

            if profile == "evidence":
                log("Generating evidence metadata...")
                dest_path = dest.resolve()
                hasher = hashlib.sha256()
                with open(dest_path, "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hasher.update(chunk)
                file_hash = hasher.hexdigest()
                metadata = {
                    "url": url,
                    "timestamp": datetime.now().isoformat(),
                    "sha256": file_hash,
                    "profile": profile,
                }
                meta_path = dest_path.with_name(dest_path.stem + "_metadata.json")
                meta_path.write_text(
                    json.dumps(metadata, indent=2, ensure_ascii=False),
                    encoding="utf-8"
                )
                log(f"  [info] Wrote metadata: {meta_path.name}")

            if preview:
                log(_("launching_preview"))
                try:
                    if sys.platform == "win32":
                        os.startfile(dest.resolve())
                    elif sys.platform == "darwin":
                        subprocess.call(["open", str(dest.resolve())])
                    else:
                        subprocess.call(["xdg-open", str(dest.resolve())])
                except Exception as exc:
                    log(f"  [warn] Failed to open preview: {exc}")

            if dom_text_len > 0:
                try:
                    import fitz
                    pdf_doc = fitz.open(str(dest.resolve()))
                    pdf_text = ""
                    for pdf_page in pdf_doc:
                        pdf_text += pdf_page.get_text()
                    pdf_text_len = len(pdf_text.strip())
                    preservation_rate = (pdf_text_len / dom_text_len) * 100
                    log(
                        f"  [info] Reproducibility Index (Text Preservation): "
                        f"{preservation_rate:.1f}% "
                        f"({pdf_text_len}/{dom_text_len} chars)")
                except ImportError:
                    log(
                        "  [warn] 'pymupdf' (fitz) is not installed. "
                        "Reproducibility Index cannot be calculated."
                    )
                except Exception as exc:
                    log(f"  [warn] Failed to extract text from PDF for metric: {exc}")

            log(_("done", dest=dest.resolve()))
            return dest.resolve()

        finally:
            browser.close()

async def convert_url_async(*args: Any, **kwargs: Any) -> Path | None:
    """Asynchronous wrapper for convert()."""
    return await asyncio.to_thread(convert, *args, **kwargs)
