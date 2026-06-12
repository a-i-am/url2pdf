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

Most HTML-to-PDF tools either produce image-only output (no text selection/search) or miss content hidden inside scrollable containers and lazy-loaded sections. **url2pdf** solves both:

- Uses a **real Chromium browser** via [Playwright](https://playwright.dev/python/) to handle JavaScript, dynamic content, and CSS
- Automatically detects and **scrolls the deepest scrollable container** to trigger lazy loading
- Extracts that container's content and re-renders it as a clean, print-ready document
- Outputs **true text-layer PDFs** — copy, search, and highlight works

---

## Installation

```bash
pip install url2pdf
playwright install chromium
```

Requires **Python 3.10+**.

---

## Quick start

### Command line

```bash
# Basic — filename is auto-generated from the page title
url2pdf https://example.com

# Custom output path
url2pdf https://example.com -o report.pdf

# Letter paper, 85% scale, 90-second timeout
url2pdf https://example.com --format Letter --scale 0.85 --timeout 90

# Silent mode (no progress output)
url2pdf https://example.com -q
```

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

## How it works

1. **Load** — opens the URL in a headless Chromium instance and waits for the page to finish loading
2. **Scroll** — finds the deepest scrollable container and scrolls it repeatedly to trigger lazy-loaded content
3. **Rebuild** — clones the container's content into a clean `<body>` and removes overflow/fixed-position constraints
4. **Print** — uses Chromium's built-in PDF renderer to produce a text-layer PDF

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
