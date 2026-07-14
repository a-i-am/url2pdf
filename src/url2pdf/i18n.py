import locale
from typing import Any

_MESSAGES: dict[str, dict[str, str]] = {
    "en": {
        "loading": "Loading page...",
        "dismissing": "Dismissing overlays / popups...",
        "scrolling": "Scrolling to load lazy content...",
        "waiting_images": "Waiting for images...",
        "injecting": "Injecting print CSS and preparing DOM...",
        "applying_reading": "Applying reading profile heuristics...",
        "generating_pdf": "Generating PDF: {dest}",
        "done": "Done: {dest}",
        "launching_preview": "Launching preview...",
        "recipe_executing": "Executing recipe actions...",
        "recipe_scrolling_page": "  [recipe] Scrolling page to bottom...",
        "recipe_scrolling_element": "  [recipe] Scrolling element '{selector}' to bottom...",
        "recipe_clicking": "  [recipe] Clicking '{selector}'...",
        "recipe_waiting": "  [recipe] Waiting {ms}ms...",
        "gui_url": "URL:",
        "gui_save_to": "Save to:",
        "gui_browse": "Browse",
        "gui_recipe": "Recipe JSON:",
        "gui_profile": "Profile:",
        "gui_faithful": "Faithful",
        "gui_evidence": "Evidence",
        "gui_reading": "Reading",
        "gui_show_browser": "Show Browser (Headed)",
        "gui_preview_pdf": "Preview PDF",
        "gui_enable_ocr": "Enable OCR",
        "gui_log_lang": "Language:",
        "gui_lang_auto": "Auto",
        "gui_lang_ko": "KO",
        "gui_lang_en": "EN",
        "gui_convert_btn": "Convert to PDF",
        "gui_status_ready": "Ready",
        "gui_status_converting": "Converting... Please wait.",
        "gui_status_saved": "Saved: {name}",
        "gui_status_finished": "Finished (No output).",
        "gui_status_failed": "Conversion failed.",
        "gui_err_input_title": "Input Error",
        "gui_err_input_msg": "Please enter a valid URL.",
        "gui_err_ocr_req_title": "Error",
        "gui_err_ocr_req_msg": "pytesseract is required for OCR. Install url2pdf[ocr].",
        "gui_err_ocr_bin_title": "Error",
        "gui_err_ocr_bin_msg": "tesseract binary not found in PATH.",
        "gui_err_success_title": "Success",
        "gui_err_success_msg": "PDF generated successfully:\n{path}",
        "gui_err_general_title": "Error",
        "gui_err_unexpected": "Unexpected error: {err}",
    },
    "ko": {
        "loading": "페이지 로드 중...",
        "dismissing": "오버레이 / 팝업 제거 중...",
        "scrolling": "지연 로드 콘텐츠 스크롤 중...",
        "waiting_images": "이미지 로드 대기 중...",
        "injecting": "인쇄용 CSS 주입 및 DOM 준비 중...",
        "applying_reading": "Reading 프로필 휴리스틱 적용 중...",
        "generating_pdf": "PDF 생성 중: {dest}",
        "done": "완료: {dest}",
        "launching_preview": "미리보기 실행 중...",
        "recipe_executing": "Recipe 액션 실행 중...",
        "recipe_scrolling_page": "  [recipe] 페이지를 맨 아래로 스크롤합니다...",
        "recipe_scrolling_element": "  [recipe] '{selector}' 요소를 맨 아래로 스크롤합니다...",
        "recipe_clicking": "  [recipe] '{selector}' 요소 클릭...",
        "recipe_waiting": "  [recipe] {ms}ms 대기 중...",
        "gui_url": "URL:",
        "gui_save_to": "저장 위치:",
        "gui_browse": "찾아보기",
        "gui_recipe": "Recipe JSON:",
        "gui_profile": "캡처 프로필:",
        "gui_faithful": "Faithful (원본 유지)",
        "gui_evidence": "Evidence (증거 모드)",
        "gui_reading": "Reading (읽기 모드)",
        "gui_show_browser": "브라우저 창 보이기",
        "gui_preview_pdf": "완료 후 PDF 열기",
        "gui_enable_ocr": "OCR 활성화",
        "gui_log_lang": "표시 언어:",
        "gui_lang_auto": "자동(Auto)",
        "gui_lang_ko": "한국어",
        "gui_lang_en": "영어",
        "gui_convert_btn": "PDF로 변환하기",
        "gui_status_ready": "대기 중",
        "gui_status_converting": "변환 중... 잠시만 기다려주세요.",
        "gui_status_saved": "저장 완료: {name}",
        "gui_status_finished": "변환 완료 (출력 파일 없음).",
        "gui_status_failed": "변환 실패.",
        "gui_err_input_title": "입력 오류",
        "gui_err_input_msg": "올바른 URL을 입력해주세요.",
        "gui_err_ocr_req_title": "오류",
        "gui_err_ocr_req_msg": (
            "OCR을 사용하려면 pytesseract가 필요합니다. 'url2pdf[ocr]'을 설치해주세요."
        ),
        "gui_err_ocr_bin_title": "오류",
        "gui_err_ocr_bin_msg": "PATH에서 tesseract 바이너리를 찾을 수 없습니다.",
        "gui_err_success_title": "성공",
        "gui_err_success_msg": "PDF가 성공적으로 생성되었습니다:\n{path}",
        "gui_err_general_title": "오류",
        "gui_err_unexpected": "예기치 않은 오류 발생: {err}",
    },
}

def get_translator(lang: str = "auto") -> Any:
    if lang == "auto":
        try:
            loc = locale.getlocale()[0]
            if loc and loc.startswith("ko"):
                lang = "ko"
            else:
                lang = "en"
        except Exception:
            lang = "en"
    
    if lang not in _MESSAGES:
        lang = "en"

    def translate(key: str, **kwargs: Any) -> str:
        msg = _MESSAGES[lang].get(key, _MESSAGES["en"].get(key, key))
        if kwargs:
            return msg.format(**kwargs)
        return msg

    return translate
