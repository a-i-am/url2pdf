"""url2pdf - GUI using tkinter."""

import os
import shutil
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Any

from .converter import convert
from .exceptions import Url2PdfError
from .i18n import get_translator


class Url2PdfApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("url2pdf")
        self.root.geometry("550x450")
        self.root.minsize(550, 450)
        self.root.columnconfigure(1, weight=1)
        self.root.columnconfigure(2, weight=0)

        self._registry: list[tuple[Any, str]] = []

        self.lang_var = tk.StringVar(value="auto")
        self._ = get_translator("auto")

        self.lang_var.trace_add("write", self._on_lang_changed)

        # URL Input
        lbl_url = tk.Label(root)
        lbl_url.grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self._register(lbl_url, "gui_url")

        self.url_var = tk.StringVar()
        tk.Entry(
            root, textvariable=self.url_var
        ).grid(row=0, column=1, columnspan=2, sticky="ew", padx=10, pady=5)

        # Output Selection
        lbl_save = tk.Label(root)
        lbl_save.grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self._register(lbl_save, "gui_save_to")

        default_dir = Path.home() / "Downloads"
        if not default_dir.exists():
            default_dir = Path.home() / "Desktop"

        self.output_var = tk.StringVar(value=str(default_dir))
        tk.Entry(
            root, textvariable=self.output_var, state="readonly"
        ).grid(row=1, column=1, sticky="ew", padx=10, pady=5)
        
        btn_browse_out = tk.Button(root, command=self.browse_output)
        btn_browse_out.grid(row=1, column=2, sticky="w", padx=10, pady=5)
        self._register(btn_browse_out, "gui_browse")

        # Recipe Selection
        lbl_recipe = tk.Label(root)
        lbl_recipe.grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self._register(lbl_recipe, "gui_recipe")

        self.recipe_var = tk.StringVar()
        tk.Entry(
            root, textvariable=self.recipe_var, state="readonly"
        ).grid(row=2, column=1, sticky="ew", padx=10, pady=5)
        
        btn_browse_rec = tk.Button(root, command=self.browse_recipe)
        btn_browse_rec.grid(row=2, column=2, sticky="w", padx=10, pady=5)
        self._register(btn_browse_rec, "gui_browse")

        # Options
        lbl_profile = tk.Label(root)
        lbl_profile.grid(row=3, column=0, sticky="w", padx=10, pady=5)
        self._register(lbl_profile, "gui_profile")

        self.profile_var = tk.StringVar(value="faithful")
        profile_frame = tk.Frame(root)
        profile_frame.grid(row=3, column=1, sticky="w", padx=10, pady=5)
        
        rb_faith = tk.Radiobutton(profile_frame, variable=self.profile_var, value="faithful")
        rb_faith.pack(side="left")
        self._register(rb_faith, "gui_faithful")
        
        rb_evi = tk.Radiobutton(profile_frame, variable=self.profile_var, value="evidence")
        rb_evi.pack(side="left")
        self._register(rb_evi, "gui_evidence")
        
        rb_read = tk.Radiobutton(profile_frame, variable=self.profile_var, value="reading")
        rb_read.pack(side="left")
        self._register(rb_read, "gui_reading")

        self.headed_var = tk.BooleanVar(value=False)
        chk_headed = tk.Checkbutton(root, variable=self.headed_var)
        chk_headed.grid(row=4, column=1, sticky="w", padx=10, pady=5)
        self._register(chk_headed, "gui_show_browser")

        self.preview_var = tk.BooleanVar(value=False)
        chk_preview = tk.Checkbutton(root, variable=self.preview_var)
        chk_preview.grid(row=4, column=2, sticky="w", padx=10, pady=5)
        self._register(chk_preview, "gui_preview_pdf")

        self.ocr_var = tk.BooleanVar(value=False)
        chk_ocr = tk.Checkbutton(root, variable=self.ocr_var)
        chk_ocr.grid(row=5, column=1, sticky="w", padx=10, pady=5)
        self._register(chk_ocr, "gui_enable_ocr")

        lbl_lang = tk.Label(root)
        lbl_lang.grid(row=6, column=0, sticky="w", padx=10, pady=5)
        self._register(lbl_lang, "gui_log_lang")

        lang_frame = tk.Frame(root)
        lang_frame.grid(row=6, column=1, sticky="w", padx=10, pady=5)
        
        rb_lang_auto = tk.Radiobutton(lang_frame, variable=self.lang_var, value="auto")
        rb_lang_auto.pack(side="left")
        self._register(rb_lang_auto, "gui_lang_auto")
        
        rb_lang_ko = tk.Radiobutton(lang_frame, variable=self.lang_var, value="ko")
        rb_lang_ko.pack(side="left")
        self._register(rb_lang_ko, "gui_lang_ko")
        
        rb_lang_en = tk.Radiobutton(lang_frame, variable=self.lang_var, value="en")
        rb_lang_en.pack(side="left")
        self._register(rb_lang_en, "gui_lang_en")

        # Convert Button & Status
        self.convert_btn = tk.Button(
            root, command=self.start_conversion, 
            bg="#4CAF50", fg="white", font=("Arial", 10, "bold")
        )
        self.convert_btn.grid(row=7, column=1, pady=20)
        self._register(self.convert_btn, "gui_convert_btn")

        self.status_var = tk.StringVar(value=self._("gui_status_ready"))
        tk.Label(
            root, textvariable=self.status_var, fg="gray"
        ).grid(row=8, column=0, columnspan=3, padx=10, pady=5)

    def _register(self, widget: Any, key: str) -> None:
        self._registry.append((widget, key))
        widget.config(text=self._(key))

    def _on_lang_changed(self, *args: Any) -> None:
        self._ = get_translator(self.lang_var.get())
        for widget, key in self._registry:
            widget.config(text=self._(key))
        self.status_var.set(self._("gui_status_ready"))

    def browse_output(self) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialdir=self.output_var.get()
        )
        if path:
            self.output_var.set(path)

    def browse_recipe(self) -> None:
        path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json")],
        )
        if path:
            self.recipe_var.set(path)

    def start_conversion(self) -> None:
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning(self._("gui_err_input_title"), self._("gui_err_input_msg"))
            return

        if self.ocr_var.get():
            try:
                import pytesseract  # noqa: F401
            except ImportError:
                messagebox.showerror(
                    self._("gui_err_ocr_req_title"), self._("gui_err_ocr_req_msg")
                )
                return
            if not shutil.which("tesseract"):
                messagebox.showerror(
                    self._("gui_err_ocr_bin_title"), self._("gui_err_ocr_bin_msg")
                )
                return

        self.convert_btn.config(state="disabled")
        self.status_var.set(self._("gui_status_converting"))
        
        threading.Thread(target=self._run_convert, args=(url,), daemon=True).start()

    def _run_convert(self, url: str) -> None:
        output_path = self.output_var.get()
        try:
            is_dir = os.path.isdir(output_path)
            result_path = convert(
                url=url,
                output=None if is_dir else output_path,
                headless=not self.headed_var.get(),
                profile=self.profile_var.get(),
                preview=self.preview_var.get(),
                recipe=self.recipe_var.get() or None,
                ocr=self.ocr_var.get(),
                lang=self.lang_var.get(),
            )
            
            if is_dir and result_path:
                final_path = Path(output_path) / result_path.name
                if result_path.exists() and result_path.absolute() != final_path.absolute():
                    shutil.move(str(result_path), str(final_path))
                    result_path = final_path

            self.root.after(0, self._on_success, result_path)
        except Url2PdfError as e:
            self.root.after(0, self._on_error, str(e))
        except Exception as e:
            self.root.after(0, self._on_error, f"Unexpected error: {e}")

    def _on_success(self, path: Path | None) -> None:
        self.convert_btn.config(state="normal")
        if path:
            self.status_var.set(self._("gui_status_saved", name=path.name))
            messagebox.showinfo(
                self._("gui_err_success_title"), 
                self._("gui_err_success_msg", path=path)
            )
        else:
            self.status_var.set(self._("gui_status_finished"))
            
    def _on_error(self, err: str) -> None:
        self.convert_btn.config(state="normal")
        self.status_var.set(self._("gui_status_failed"))
        messagebox.showerror(self._("gui_err_general_title"), self._("gui_err_unexpected", err=err))


def main() -> None:
    root = tk.Tk()
    _ = Url2PdfApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
