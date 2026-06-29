# url2pdf

**커맨드라인 또는 Python에서 웹 페이지를 텍스트 선택·검색 가능한 진짜 PDF로 변환합니다.**

[![CI](https://github.com/a-i-am/url2pdf/actions/workflows/ci.yml/badge.svg)](https://github.com/a-i-am/url2pdf/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/url2pdf)](https://pypi.org/project/url2pdf/)
[![Python](https://img.shields.io/pypi/pyversions/url2pdf)](https://pypi.org/project/url2pdf/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

> English README: [README.md](README.md)

---

## 왜 url2pdf인가?

대부분의 HTML→PDF 도구는 이미지로만 출력하거나(텍스트 선택 불가), 스크롤 컨테이너 안쪽 내용과 지연 로딩 콘텐츠를 놓칩니다. **url2pdf**는 두 문제를 모두 해결합니다.

### ✨ 주요 기능 (Features)
- **실제 브라우저 렌더링:** [Playwright](https://playwright.dev/python/)를 통해 실제 Chromium 브라우저를 구동하여 JavaScript, 동적 콘텐츠, 최신 CSS를 완벽하게 지원합니다.
- **지연 로딩(Lazy-Load) 완벽 대응:** 가장 깊은 스크롤 컨테이너를 자동으로 감지하고 반복 스크롤하여 이미지나 무한 리스트 등의 지연 로딩 콘텐츠를 모두 불러옵니다.
- **진짜 PDF 출력:** 이미지 통짜 PDF가 아닌, 텍스트 레이어가 살아있는 진짜 PDF를 출력합니다. 일반 문서처럼 텍스트 복사, 검색, 형광펜 기능이 모두 동작합니다.
- **철저한 개인정보 보호:** 모든 변환 작업은 사용자의 로컬 환경에서만 수행됩니다. URL, IP, 변환된 PDF 내용 등 어떠한 사용자 데이터도 외부 서버로 전송되지 않습니다.

---

## 설치

```bash
pip install url2pdf
playwright install chromium
```

* **Python 3.10 이상**이 필요합니다. url2pdf 패키지 자체는 매우 가볍지만(~15KB), 첫 설치 시 Playwright 구동을 위한 Chromium 브라우저 바이너리(약 100~150MB) 다운로드가 필요합니다.*

---

## 빠른 시작

### 커맨드라인

```bash
# 기본 사용 — 파일명은 페이지 제목에서 자동 생성
url2pdf https://example.com

# 저장 경로 지정
url2pdf https://example.com -o report.pdf

# Letter 용지, 85% 배율, 90초 타임아웃
url2pdf https://example.com --format Letter --scale 0.85 --timeout 90

# 조용한 모드 (진행 메시지 없음)
url2pdf https://example.com -q
```

### Python API

```python
from url2pdf import convert

# 생성된 파일의 pathlib.Path를 반환
path = convert("https://example.com")
print(f"저장됨: {path}")

# 전체 옵션
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

## CLI 옵션

| 플래그 | 기본값 | 설명 |
|--------|--------|------|
| `url` | *(필수)* | 변환할 URL |
| `-o / --output` | 자동 | 출력 PDF 경로 |
| `--format` | `A4` | 용지 형식 (`A4`, `Letter`, `A3`, …) |
| `--scale` | `0.9` | CSS 배율 (0.1 – 2.0) |
| `--timeout` | `60` | 페이지 로드 타임아웃 (초) |
| `--scroll-rounds` | `80` | 지연 콘텐츠용 최대 스크롤 횟수 |
| `-q / --quiet` | 꺼짐 | 진행 메시지 숨기기 |

---

## 동작 원리 (Tech Stack)

**url2pdf**는 **Python**, **Playwright**, **pytest**를 기반으로 개발되었습니다.
1. **로드** — 헤드리스 Chromium으로 URL을 열고 페이지 로딩이 완료될 때까지 대기합니다.
2. **스크롤** — 가장 깊은 스크롤 컨테이너를 찾아 반복 스크롤해 지연 로딩 콘텐츠를 모두 활성화합니다.
3. **재구성** — 해당 컨테이너 내용을 깨끗한 `<body>`로 이식하고 overflow·고정 위치 제약을 제거합니다.
4. **출력** — Chromium 내장 PDF 렌더러로 텍스트 레이어가 포함된 고품질 PDF를 생성합니다.

---

## 한계점 (Limitations)

- **로그인 및 세션:** 현재 로그인이 필요한 페이지나 활성화된 세션 유지가 필요한 사이트는 지원하지 않습니다 (단, API로 직접 쿠키를 주입하는 경우는 예외).
- **봇 방지 시스템:** Cloudflare Turnstile, reCAPTCHA 등 강력한 봇 방지 화면이 있는 사이트는 헤드리스 브라우저 접근을 차단할 수 있습니다.
- **무한 스크롤:** 끝이 없는 웹 페이지의 경우 무한 루프를 방지하기 위해 `--scroll-rounds` 인자를 통해 스크롤 횟수가 제한됩니다.

---

## 업데이트 계획 (Roadmap)

url2pdf는 지속적으로 개선될 예정입니다. 향후 릴리즈(v1.1.0+)에서 다음 기능들이 추가될 계획입니다:

- **GUI 프로그램 제공:** CLI 환경이 낯선 일반 사용자를 위해 클릭만으로 변환 가능한 데스크톱/웹 기반 UI를 제공할 예정입니다.
- **지원 도메인 사전 확인 기능:** `url2pdf --check <url>` 명령어를 통해 변환 성공률이 높은(검증된) 도메인인지 프로그램 내에서 바로 확인할 수 있는 기능을 지원합니다.
- **일괄 변환 (Bulk Conversion):** `.txt`나 `.csv` 파일로 여러 링크를 입력받아 대량으로 변환하는 기능을 지원합니다.
- **비동기(Async) 지원:** FastAPI 등 비동기 Python 애플리케이션과의 원활한 통합을 위한 비동기 API를 제공할 예정입니다.
- **AI 통합 기능 (예정):**
  - *스마트 콘텐츠 추출*: LLM을 활용해 렌더링 전 광고나 네비게이션 바 등 불필요한 요소를 식별하고 제거합니다.
  - *자동 요약*: `--summarize` 옵션을 통해 페이지 내용의 AI 요약본을 생성하여 PDF 마지막 장에 추가합니다.
- **다국어 및 자동 감지 (i18n):** 사용자의 OS 로캘 환경을 감지하여 CLI 메시지가 한국어/영어로 자동 출력되도록 개선합니다.
- **기본 저장 경로 설정:** 바탕화면이나 다운로드 폴더로 자동 저장되도록 지원합니다.

---

## 오류 처리

url2pdf는 타입이 있는 예외를 발생시킵니다:

```python
from url2pdf import convert
from url2pdf.exceptions import PageLoadError, PDFGenerationError

try:
    convert("https://example.com", output="out.pdf")
except PageLoadError as e:
    print(f"페이지를 열 수 없습니다: {e}")
except PDFGenerationError as e:
    print(f"PDF 생성 실패: {e}")
```

---

## 개발 참여

프로젝트 시작일: **2026년 6월 11일** | 첫 릴리즈(v1.0.0): **2026년 6월 30일**

```bash
git clone https://github.com/a-i-am/url2pdf
cd url2pdf
pip install -e ".[dev]"
playwright install chromium

# 테스트 실행
pytest

# 린트 + 타입 검사
ruff check src tests
mypy src
```

버그 리포트와 풀 리퀘스트 환영합니다!  
큰 변경 사항은 먼저 [이슈](https://github.com/a-i-am/url2pdf/issues)를 열어 논의해 주세요.

---

## 라이선스

[MIT](LICENSE) © Sieun Park
