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

- [Playwright](https://playwright.dev/python/)를 통해 **실제 Chromium 브라우저**를 구동 — JavaScript·동적 콘텐츠·CSS 완전 지원
- 가장 깊은 스크롤 컨테이너를 자동으로 감지하고 반복 스크롤해 **지연 로딩 콘텐츠** 를 모두 불러옴
- 해당 컨테이너 내용만 추출해 깔끔한 인쇄용 문서로 재구성
- **텍스트 레이어가 있는 진짜 PDF** 출력 — 복사·검색·형광펜 모두 동작

---

## 설치

```bash
pip install url2pdf
playwright install chromium
```

**Python 3.10 이상** 필요.

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

## 동작 원리

1. **로드** — 헤드리스 Chromium으로 URL을 열고 페이지 로딩이 완료될 때까지 대기
2. **스크롤** — 가장 깊은 스크롤 컨테이너를 찾아 반복 스크롤해 지연 로딩 콘텐츠 활성화
3. **재구성** — 해당 컨테이너 내용을 깨끗한 `<body>`로 이식하고 overflow·고정 위치 제약 제거
4. **출력** — Chromium 내장 PDF 렌더러로 텍스트 레이어 PDF 생성

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
