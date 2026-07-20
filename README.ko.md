# url2pdf

**웹 페이지를 커맨드라인, Python, 데스크톱 GUI에서 검색 가능한 PDF로 변환합니다.**

[![CI](https://github.com/a-i-am/url2pdf/actions/workflows/ci.yml/badge.svg)](https://github.com/a-i-am/url2pdf/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/url2pdf)](https://pypi.org/project/url2pdf/)
[![Python](https://img.shields.io/pypi/pyversions/url2pdf)](https://pypi.org/project/url2pdf/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> English README: [README.md](README.md)

## 데모

![url2pdf 데모](docs/demo.gif)

## 주요 기능

- Playwright Chromium 기반 실제 브라우저 렌더링.
- 스크롤 중 로드되는 지연 콘텐츠 대응.
- 일반 HTML 페이지에서 텍스트 선택과 검색이 가능한 PDF 생성.
- 데스크톱 GUI: `url2pdf-gui`.
- 캡처 프로필: 원본 유지, 증거 메타데이터, 읽기 모드.
- 캡처 전 클릭, 대기, 스크롤을 실행하는 Recipe JSON.
- 이미지 중심 페이지용 Tesseract OCR 모드.
- PDF 레이아웃 선택: 일반 페이지 나누기 또는 긴 1페이지.
- 배치 변환, 세션 파일, 미리보기, 연결 확인 모드.

모든 변환은 로컬에서 실행됩니다. url2pdf는 URL이나 PDF 내용을 외부 서비스로 보내지 않습니다.

## 설치

```bash
pip install url2pdf
playwright install chromium
```

OCR은 선택 의존성과 Tesseract 바이너리가 필요합니다.

```bash
pip install "url2pdf[ocr]"
```

Tesseract는 별도로 설치해야 합니다. 한국어 OCR은 `kor+eng`을 사용하고 Korean trained data를 설치해야 합니다.

Python 3.10 이상이 필요합니다.

## 빠른 시작

```bash
# 기본 PDF
url2pdf https://example.com

# 저장 경로 지정
url2pdf https://example.com -o report.pdf

# 데스크톱 GUI 실행
url2pdf-gui

# 페이지를 나누지 않고 긴 1페이지 PDF 생성
url2pdf https://example.com --pdf-layout single

# 이미지 중심 페이지 OCR PDF
url2pdf https://example.com --ocr --ocr-lang eng

# 한국어 + 영어 OCR
url2pdf https://example.com --ocr --ocr-lang kor+eng

# 캡처 전 레시피 실행
url2pdf https://example.com --recipe actions.json

# PDF 생성 없이 레시피를 눈으로 테스트
url2pdf https://example.com --recipe actions.json --test-recipe

# 텍스트 파일의 URL 목록 일괄 변환
url2pdf --batch urls.txt
```

## GUI

실행:

```bash
url2pdf-gui
```

GUI는 URL 입력, 저장 위치 선택, 캡처 프로필, PDF 미리보기, Recipe JSON, OCR 언어, Tesseract 경로, PDF 레이아웃 선택을 지원합니다.

## Recipe JSON

Recipe JSON은 PDF 캡처 전에 작은 브라우저 동작을 실행합니다.

```json
[
  { "action": "wait", "ms": 2000 },
  { "action": "click", "selector": "#agree-btn", "optional": true },
  { "action": "scroll" }
]
```

지원 액션:

| 액션 | 필드 | 설명 |
|---|---|---|
| `wait` | `ms` | 0-60000 밀리초 대기합니다. |
| `click` | `selector`, `optional` | CSS 선택자를 클릭합니다. optional이면 요소가 없어도 무시합니다. |
| `scroll` | `selector` 선택 | 페이지 또는 선택한 스크롤 컨테이너를 스크롤합니다. |

내장 프리셋:

```bash
url2pdf https://example.com --recipe dismiss-cookies
url2pdf https://example.com --recipe lazy-load
url2pdf https://example.com --help-recipe
```

## CLI 옵션

| 플래그 | 기본값 | 설명 |
|---|---|---|
| `url` | `--batch` 사용 시 선택 | 변환할 URL. |
| `-o`, `--output` | 페이지 제목 | 출력 PDF 경로 또는 폴더. |
| `--batch FILE` | 꺼짐 | 텍스트 파일의 URL 목록을 일괄 변환합니다. |
| `--check` | 꺼짐 | HTTP 연결만 확인합니다. |
| `--format FORMAT` | `A4` | `A4`, `Letter`, `A3` 같은 용지 형식. |
| `--pdf-layout pages\|single` | `pages` | 일반 페이지 나누기 또는 긴 1페이지. |
| `--scale SCALE` | `0.9` | PDF 배율, 0.1부터 2.0까지. |
| `--timeout SECONDS` | `60` | 페이지 로드 타임아웃. |
| `--scroll-rounds N` | `80` | 지연 콘텐츠용 최대 스크롤 횟수. |
| `--profile faithful\|evidence\|reading` | `faithful` | 캡처 프로필. |
| `--preview` | 꺼짐 | 생성된 PDF를 OS 기본 뷰어로 엽니다. |
| `--recipe FILE_OR_PRESET` | 꺼짐 | 캡처 전 레시피 액션을 실행합니다. |
| `--help-recipe` | 꺼짐 | 레시피 도움말을 표시합니다. |
| `--test-recipe` | 꺼짐 | 레시피를 보이는 브라우저에서 실행하고 PDF는 만들지 않습니다. |
| `--ocr` | 꺼짐 | 전체 페이지 스크린샷 기반 OCR PDF를 생성합니다. |
| `--ocr-lang LANG` | `eng` | Tesseract 언어. 예: `eng`, `kor+eng`. |
| `--tesseract-cmd PATH` | 자동 | Tesseract 실행 파일 경로. |
| `--session FILE` | 꺼짐 | 로그인 세션용 Playwright `storageState.json`. |
| `--headed` | 꺼짐 | 변환 중 Chromium 창을 표시합니다. |
| `--manual-verification` | 꺼짐 | 브라우저 인증 화면이 감지되면 수동 확인을 기다립니다. |
| `--lang auto\|ko\|en` | `auto` | CLI와 GUI 메시지 언어. |
| `-q`, `--quiet` | 꺼짐 | 진행 메시지를 숨깁니다. |

## Python API

```python
from url2pdf import convert

path = convert(
    "https://example.com",
    output="report.pdf",
    page_format="A4",
    pdf_layout="pages",
    profile="faithful",
    timeout=60,
)

print(path)
```

OCR:

```python
from url2pdf import convert

convert(
    "https://example.com",
    output="ocr.pdf",
    ocr=True,
    ocr_lang="kor+eng",
    tesseract_cmd=r"C:\Program Files\Tesseract-OCR\tesseract.exe",
)
```

## 한계

- OCR 품질은 Tesseract, 설치된 언어 데이터, 원본 이미지 품질, PDF 뷰어에 영향을 받습니다. 검색은 되더라도 선택 영역 위치가 완벽하지 않을 수 있습니다.
- 봇 방지, 유료 장벽, 강한 자동화 차단 사이트는 `--headed`, `--manual-verification`, 세션 파일이 필요할 수 있습니다.
- Reading 모드는 휴리스틱입니다. 특이한 페이지에서는 필요한 콘텐츠를 제거할 수 있습니다.
- 매우 긴 이미지 중심 페이지는 OCR PDF 파일이 커질 수 있습니다.

## 개발

```bash
git clone https://github.com/a-i-am/url2pdf
cd url2pdf
pip install -e ".[dev,ocr]"
playwright install chromium

pytest
ruff check src tests
mypy src
python -m build
```

## 릴리즈 노트

### v1.2.1

- `url2pdf-gui` 데스크톱 GUI를 추가했습니다.
- OCR 언어와 Tesseract 경로 옵션을 추가했습니다.
- `--pdf-layout pages|single` 옵션을 추가했습니다.
- GUI 레시피 빌더/도움말과 CLI 레시피 테스트 모드를 추가했습니다.
- 페이지 잘림, 지연 이미지, 웹 폰트, 오버레이, 넓은 레이아웃 처리를 개선했습니다.
- GUI 옵션 전달, OCR 텍스트 정규화, 레이아웃 옵션에 대한 회귀 테스트를 추가했습니다.

## 라이선스

[MIT](LICENSE) © Sieun Park
