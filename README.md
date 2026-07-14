# url2pdf

**Convert any web page to a searchable, text-selectable PDF — from the command line or Python.**

[![CI](https://github.com/a-i-am/url2pdf/actions/workflows/ci.yml/badge.svg)](https://github.com/a-i-am/url2pdf/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/url2pdf)](https://pypi.org/project/url2pdf/)
[![Python](https://img.shields.io/pypi/pyversions/url2pdf)](https://pypi.org/project/url2pdf/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

> 한국어 README는 [README.ko.md](README.ko.md)를 참고하세요.

---

## Why url2pdf?

Most HTML-to-PDF tools either produce image-only output (no text selection/search) or miss content hidden inside scrollable containers and lazy-loaded sections. **url2pdf** solves both.

### ✨ Features
- **Real Browser Rendering:** Uses a real Chromium browser via [Playwright](https://playwright.dev/python/) to perfectly handle JavaScript, dynamic content, and modern CSS.
- **Lazy-Load Triggering:** Automatically detects and scrolls the deepest scrollable container to ensure all lazy-loaded content (images, infinite lists) is fully loaded.
- **True PDF Output:** Outputs true text-layer PDFs, meaning you can search, copy, and highlight text just like a native document.
- **Privacy First:** All conversions happen locally on your machine. No URLs, IPs, or PDF contents are collected or sent to any external servers.

---

## Installation

To install the core tool:
```bash
pip install url2pdf
```

To use the `--ocr` feature for image-heavy pages, install the optional `ocr` dependency:
```bash
pip install "url2pdf[ocr]"
```
*Note: You must also install the `tesseract` binary on your system (e.g., `apt install tesseract-ocr` or via the Windows installer) for the `--ocr` feature to work.*

```bash
playwright install chromium
```

*Requires **Python 3.10+**. The url2pdf package itself is very lightweight (approx. 15KB), but it requires downloading the Playwright Chromium browser binaries (approx. 100-150MB) on the first install.*

---

## Quick start

### Command line

```bash
# 기본 사용 (faithful 프로필)
url2pdf https://example.com

# 캡처 프로필 지정 및 PDF 미리보기
url2pdf https://example.com --profile reading --preview

# 로그인 세션 유지 (미리 저장된 storageState.json 사용)
url2pdf https://github.com --session session.json

# 커스텀 동작 (레시피) 실행
url2pdf https://example.com --recipe actions.json

# OCR을 사용해 이미지 중심 페이지 캡처 (pytesseract 및 tesseract 바이너리 필요)
# 긴 페이지의 경우 스크린샷 이미지 크기나 타임아웃 제한으로 인해 실패할 수 있습니다.
url2pdf https://example.com --ocr --ocr-lang kor+eng

# CLI 출력 언어 지정 (기본값: auto)
url2pdf https://example.com --lang ko
```

* `--profile`: 캡처 프로필을 지정합니다.
  * `faithful` (기본값): 화면에 보이는 그대로 캡처합니다.
  * `evidence`: 캡처 후 원본 URL과 SHA-256 해시가 포함된 메타데이터 JSON 파일을 함께 생성합니다.
  * `reading`: 광고, 내비게이션 바 등 불필요한 요소를 제거하고 본문 위주로 캡처합니다. (※ 휴리스틱 기반으로 작동하므로 사이트 구조에 따라 완벽하게 제거되지 않거나 본문 일부가 누락될 수 있는 한계가 있습니다.)

* `--preview`: 변환 완료 후 생성된 PDF를 OS 기본 뷰어로 즉시 열어 확인합니다.

### Python API

```python
from url2pdf import convert

# Returns pathlib.Path of the generated file
path = convert("https://example.com")
print(f"Saved to {path}")

# Full options
path = convert(
    "https://example.com",
    output="report.pdf",
    timeout=90,
    page_format="Letter",
    scale=0.85,
    verbose=False,
)
```

---

## CLI reference

| Flag | Default | Description |
|------|---------|-------------|
| `url` | *(required)* | URL to convert |
| `-o / --output` | auto | Output PDF path |
| `--format` | `A4` | Paper format (`A4`, `Letter`, `A3`, …) |
| `--scale` | `0.9` | CSS scale factor (0.1 – 2.0) |
| `--timeout` | `60` | Page load timeout in seconds |
| `--scroll-rounds` | `80` | Max scroll iterations for lazy content |
| `-q / --quiet` | off | Suppress progress messages |

---

## How it works (Tech Stack)

**url2pdf** is built with **Python**, **Playwright**, and **pytest**.
1. **Load** — opens the URL in a headless Chromium instance and waits for the page to finish loading.
2. **Scroll** — finds the deepest scrollable container and scrolls it repeatedly to trigger lazy-loaded content.
3. **Rebuild** — clones the container's content into a clean `<body>` and removes overflow/fixed-position constraints.
4. **Print** — uses Chromium's built-in PDF renderer to produce a text-layer PDF.

---

## Limitations

- **Authentication:** Sites requiring login or active sessions are not currently supported (unless cookies are injected manually via API).
- **Anti-Bot Protection:** Sites with strict Cloudflare Turnstile, reCAPTCHA, or similar bot-protection screens may block the headless browser.
- **Infinite Scrolling:** Endless web pages are limited by the `--scroll-rounds` parameter to prevent infinite loops.

---

## Roadmap

We are constantly improving `url2pdf`. Here is what is planned for future releases (v1.1.0+):

- **GUI Version:** A user-friendly desktop or web wrapper for non-CLI users.
- **Supported Domains Checker:** A built-in command (`url2pdf --check <url>`) to verify if a domain is known to convert stably.
- **Bulk Conversion:** Convert a list of URLs sequentially from a `.txt` or `.csv` file.
- **Async Support:** Asynchronous API for better integration into async Python applications (FastAPI, etc.).
- **AI Integration (Planned):** 
  - *Smart Content Extraction*: Use LLMs to identify and remove boilerplate (ads, navbars) before PDF generation.
  - *Auto-Summarization*: A `--summarize` flag to generate and append an AI summary of the page to the final PDF.
- **i18n & Auto-Language:** CLI messages will automatically adapt to your OS locale (e.g., English / Korean).
- **Default Save Path:** Configure a global default save directory (like `~/Downloads`).

---

## Error handling

url2pdf raises typed exceptions you can catch:

```python
from url2pdf import convert
from url2pdf.exceptions import PageLoadError, PDFGenerationError

try:
    convert("https://example.com", output="out.pdf")
except PageLoadError as e:
    print(f"Could not load page: {e}")
except PDFGenerationError as e:
    print(f"PDF generation failed: {e}")
```

---

## Development

Project started: **June 11, 2026** | First release (v1.0.0): **June 30, 2026**

```bash
git clone https://github.com/a-i-am/url2pdf
cd url2pdf
pip install -e ".[dev]"
playwright install chromium

# Run tests
pytest

# Lint + type-check
ruff check src tests
mypy src
```

---

## Contributing

Bug reports and pull requests are welcome!  
Please open an [issue](https://github.com/a-i-am/url2pdf/issues) before submitting a large change.

---

## License

[MIT](LICENSE) © Sieun Park
