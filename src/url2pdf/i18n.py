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
        "gui_recipe_builder_title": "Recipe Builder",
        "gui_recipe_wait_title": "Wait",
        "gui_recipe_wait_prompt": "Milliseconds to wait (e.g., 2000):",
        "gui_recipe_click_title": "Click",
        "gui_recipe_click_prompt": "CSS Selector to click (e.g., .cookie-btn):",
        "gui_recipe_err_empty_title": "Empty",
        "gui_recipe_err_empty_msg": "No actions added.",
        "gui_recipe_err_save_title": "Error",
        "gui_recipe_err_save_msg": "Failed to save recipe: {e}",
        "gui_recipe_save_btn": "Save JSON",
        "gui_recipe_scroll": "Scroll",
        "gui_recipe_wait": "Wait",
        "gui_recipe_click": "Click",
        "gui_recipe_help_title": "Recipe JSON Guide",
        "gui_recipe_help_msg": (
            "Recipe JSON allows you to automate clicks, waits, and scrolling "
            "before capturing the PDF.\n"
            "You can use a custom JSON file path, or one of the built-in presets.\n\n"
            "Built-in Presets:\n"
            "  dismiss-cookies : Attempts to close common cookie/GDPR consent banners.\n"
            "  lazy-load       : Scrolls down the page once to trigger lazy-loaded images.\n\n"
            "Creating Custom Recipes:\n"
            "Write a JSON array of objects, e.g.:\n"
            "[\n"
            '  { "action": "wait", "ms": 2000 },\n'
            '  { "action": "click", "selector": "#agree-btn", "optional": true },\n'
            '  { "action": "scroll" }\n'
            "]\n\n"
            "Actions:\n"
            "- wait: wait for 'ms' milliseconds.\n"
            "- click: click element matching 'selector'. If 'optional' is true, ignores errors.\n"
            "- scroll: scroll to bottom of the page or specific 'selector'.\n\n"
            "You can enter the preset name (e.g., dismiss-cookies) directly "
            "into the 'Recipe JSON' input field!"
        ),
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
        "gui_recipe_builder_title": "레시피 빌더",
        "gui_recipe_wait_title": "대기(Wait)",
        "gui_recipe_wait_prompt": "대기할 시간 (밀리초 단위, 예: 2000):",
        "gui_recipe_click_title": "클릭(Click)",
        "gui_recipe_click_prompt": "클릭할 CSS 선택자 (예: .cookie-btn):",
        "gui_recipe_err_empty_title": "비어 있음",
        "gui_recipe_err_empty_msg": "추가된 액션이 없습니다.",
        "gui_recipe_err_save_title": "오류",
        "gui_recipe_err_save_msg": "레시피 저장 실패: {e}",
        "gui_recipe_save_btn": "JSON 저장",
        "gui_recipe_scroll": "스크롤(Scroll)",
        "gui_recipe_wait": "대기(Wait)",
        "gui_recipe_click": "클릭(Click)",
        "gui_recipe_help_title": "레시피 JSON 가이드",
        "gui_recipe_help_msg": (
            "레시피 JSON을 사용하면 PDF 캡처 전에 클릭, 대기, 스크롤 동작을 자동화할 수 있습니다.\n"
            "직접 만든 JSON 파일을 선택하거나, 내장 프리셋을 사용할 수 있습니다.\n\n"
            "내장 프리셋:\n"
            "  dismiss-cookies : 쿠키/GDPR 동의 배너를 자동으로 닫으려 시도합니다.\n"
            "  lazy-load       : 지연 로딩되는 이미지를 불러오기 위해 페이지를 "
            "한 번 스크롤합니다.\n\n"
            "커스텀 레시피 생성:\n"
            "다음과 같이 객체의 JSON 배열을 작성합니다:\n"
            "[\n"
            '  { "action": "wait", "ms": 2000 },\n'
            '  { "action": "click", "selector": "#agree-btn", "optional": true },\n'
            '  { "action": "scroll" }\n'
            "]\n\n"
            "지원되는 액션:\n"
            "- wait: 'ms' 밀리초 동안 대기합니다.\n"
            "- click: 'selector' 요소 클릭. 'optional'이 true이면 찾지 못해도 무시합니다.\n"
            "- scroll: 페이지 맨 아래 또는 특정 'selector'로 스크롤합니다.\n\n"
            "'Recipe JSON' 입력란에 프리셋 이름(예: dismiss-cookies)을 직접 입력하셔도 됩니다!"
        ),
    },
}

def get_translator(lang: str = "auto") -> Any:
    if lang == "auto":
        try:
            loc = locale.getlocale()[0]
            if not loc:
                import sys
                if sys.platform == "win32":
                    import ctypes
                    langid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
                    # 1042 is Korean
                    if langid == 1042:
                        loc = "ko"
            
            if loc and (loc.lower().startswith("ko") or loc.lower().startswith("korean")):
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
