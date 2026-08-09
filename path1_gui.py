"""video-autopilot-kit Path 1 的 Windows-first Tkinter 桌面介面。"""
from __future__ import annotations

import argparse
import contextlib
import json
import os
import queue
import subprocess
import sys
import threading
import traceback
from collections.abc import Callable
from pathlib import Path

from path1_core import (
    APP_VERSION,
    OperationResult,
    dependency_status,
    load_settings,
    parse_screen_clean_options,
    parse_teardown_options,
    run_delivery_qa_job,
    run_screen_clean_job,
    run_short_job,
    run_teardown_job,
    save_settings,
)

WORKFLOWS = {
    "shorts_scan": "Shorts 素材掃描",
    "shorts_build": "Shorts 成片建置",
    "teardown": "競品節奏量測",
    "delivery_qa": "交付 QA",
    "screen_clean": "螢幕錄影清理",
    "health": "依賴健檢",
}


class QueueWriter:
    """將既有核心的 print 輸出安全轉送到 Tk 主執行緒。"""

    def __init__(self, events: queue.Queue) -> None:
        self.events = events

    def write(self, value: str) -> int:
        if value:
            self.events.put(("log", value))
        return len(value)

    def flush(self) -> None:
        return None


class Path1GUI:
    """Path 1 工作台；所有長時間影音工作都在背景 thread 執行。"""

    def __init__(self, root) -> None:
        import tkinter as tk
        from tkinter import ttk

        self.root = root
        self.tk = tk
        self.ttk = ttk
        self.events: queue.Queue = queue.Queue()
        self.running = False
        self.run_buttons = []
        self.last_output: Path | None = None
        self.settings = load_settings()

        root.title(f"video-autopilot-kit · Path 1 工作台 v{APP_VERSION}")
        root.minsize(980, 700)
        root.geometry("1180x820")
        self._maximize_window()
        self._configure_style()
        self._create_variables()
        self._build_menu()
        self._build_layout()
        root.protocol("WM_DELETE_WINDOW", self.close)
        root.after(80, self._poll_events)
        root.after(250, self.refresh_dependencies)

    def _maximize_window(self) -> None:
        try:
            self.root.state("zoomed")
        except self.tk.TclError:
            pass

    def _configure_style(self) -> None:
        style = self.ttk.Style(self.root)
        try:
            style.theme_use("vista" if sys.platform == "win32" else "clam")
        except self.tk.TclError:
            pass
        style.configure("App.TFrame", background="#f3f6fa")
        style.configure("Header.TFrame", background="#152238")
        style.configure(
            "Title.TLabel",
            background="#152238",
            foreground="#ffffff",
            font=("Microsoft JhengHei UI", 20, "bold"),
        )
        style.configure(
            "Subtitle.TLabel",
            background="#152238",
            foreground="#b9c9de",
            font=("Microsoft JhengHei UI", 10),
        )
        style.configure(
            "Section.TLabelframe.Label",
            foreground="#183153",
            font=("Microsoft JhengHei UI", 11, "bold"),
        )
        style.configure("Primary.TButton", font=("Microsoft JhengHei UI", 10, "bold"))
        style.configure("Status.TLabel", font=("Microsoft JhengHei UI", 10, "bold"))
        style.configure("Hint.TLabel", foreground="#52657d", font=("Microsoft JhengHei UI", 9))
        style.configure("TNotebook.Tab", padding=(16, 8), font=("Microsoft JhengHei UI", 10))

    def _value(self, key: str, default: str = "") -> str:
        value = self.settings.get(key, default)
        return str(value) if value is not None else default

    def _create_variables(self) -> None:
        StringVar = self.tk.StringVar
        BooleanVar = self.tk.BooleanVar
        self.project_var = StringVar(value=self._value("project_dir"))
        self.bgm_var = StringVar(value=self._value("bgm_dir"))
        self.teardown_target_var = StringVar(value=self._value("teardown_target"))
        self.band_var = StringVar(value=self._value("band", "wide"))
        self.threshold_var = StringVar(value=self._value("threshold", "0.25"))
        self.qa_video_var = StringVar(value=self._value("qa_video"))
        self.qa_audio_var = BooleanVar(value=bool(self.settings.get("qa_audio", True)))
        self.clean_source_var = StringVar(value=self._value("clean_source"))
        self.clean_output_var = StringVar(value=self._value("clean_output"))
        self.crop_var = StringVar(value=self._value("crop", "1920:930:0:100"))
        self.head_trim_var = StringVar(value=self._value("head_trim", "1.0"))
        self.tail_trim_var = StringVar(value=self._value("tail_trim", "2.0"))
        self.status_var = StringVar(value="準備就緒")
        self.dependency_var = StringVar(value="正在檢查內嵌依賴…")

    def _build_menu(self) -> None:
        menu = self.tk.Menu(self.root)
        file_menu = self.tk.Menu(menu, tearoff=False)
        file_menu.add_command(label="開啟最近輸出", command=self.open_last_output)
        file_menu.add_command(label="匯出執行日誌…", command=self.export_log)
        file_menu.add_separator()
        file_menu.add_command(label="結束", command=self.close)
        menu.add_cascade(label="檔案", menu=file_menu)
        help_menu = self.tk.Menu(menu, tearoff=False)
        help_menu.add_command(label="關於 Path 1 工作台", command=self.show_about)
        menu.add_cascade(label="說明", menu=help_menu)
        self.root.configure(menu=menu)

    def _build_layout(self) -> None:
        ttk = self.ttk
        shell = ttk.Frame(self.root, style="App.TFrame", padding=0)
        shell.pack(fill="both", expand=True)

        header = ttk.Frame(shell, style="Header.TFrame", padding=(24, 17))
        header.pack(fill="x")
        ttk.Label(header, text="Path 1 · Programmatic 工作台", style="Title.TLabel").pack(
            anchor="w"
        )
        ttk.Label(
            header,
            text="純 Python + ffmpeg｜不需要 CapCut｜素材留在本機",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(3, 0))

        status_bar = ttk.Frame(shell, padding=(20, 10, 20, 7))
        status_bar.pack(fill="x")
        ttk.Label(status_bar, textvariable=self.status_var, style="Status.TLabel").pack(
            side="left"
        )
        ttk.Label(status_bar, textvariable=self.dependency_var, style="Hint.TLabel").pack(
            side="right"
        )

        notebook = ttk.Notebook(shell)
        notebook.pack(fill="both", expand=True, padx=20)
        self.notebook = notebook
        self._build_shorts_tab(notebook)
        self._build_tools_tab(notebook)
        self._build_health_tab(notebook)

        log_frame = ttk.LabelFrame(
            shell,
            text="執行日誌",
            style="Section.TLabelframe",
            padding=(10, 7),
        )
        log_frame.pack(fill="both", padx=20, pady=(10, 15))
        self.log = self.tk.Text(
            log_frame,
            height=9,
            wrap="word",
            font=("Cascadia Mono", 9),
            background="#0e1726",
            foreground="#d8e4f2",
            insertbackground="#ffffff",
            relief="flat",
            padx=10,
            pady=8,
        )
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=scrollbar.set)
        self.log.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self._append_log("Path 1 工作台已啟動。先確認右上角依賴狀態，再選擇工作流程。\n")

    def _build_shorts_tab(self, notebook) -> None:
        ttk = self.ttk
        tab = ttk.Frame(notebook, padding=18)
        notebook.add(tab, text="Shorts Autopilot")
        tab.columnconfigure(0, weight=3)
        tab.columnconfigure(1, weight=2)

        form = ttk.LabelFrame(tab, text="直式 Shorts 專案", padding=14)
        form.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        form.columnconfigure(1, weight=1)
        self._path_row(form, 0, "專案資料夾", self.project_var, self._browse_project)
        self._path_row(form, 1, "BGM 素材庫", self.bgm_var, self._browse_bgm)
        ttk.Label(
            form,
            text="專案資料夾直接放原始 MP4/MOV；BGM 素材庫依 _plan.py 的 bgm_folder 分類。",
            style="Hint.TLabel",
            wraplength=680,
        ).grid(row=2, column=0, columnspan=3, sticky="w", pady=(5, 13))

        buttons = ttk.Frame(form)
        buttons.grid(row=3, column=0, columnspan=3, sticky="w")
        self._run_button(buttons, "① 掃描素材", lambda: self.start_short("scan"), True).pack(
            side="left", padx=(0, 8)
        )
        ttk.Button(buttons, text="② 開啟 _plan.py", command=self.open_plan).pack(
            side="left", padx=(0, 8)
        )
        self._run_button(buttons, "③ 建置 + QA", lambda: self.start_short("build"), True).pack(
            side="left", padx=(0, 8)
        )
        ttk.Button(buttons, text="開啟輸出", command=self.open_short_output).pack(side="left")

        guide = ttk.LabelFrame(tab, text="三步驟", padding=14)
        guide.grid(row=0, column=1, sticky="nsew")
        steps = (
            ("1", "掃描", "正規化 9:16、接觸表、招牌放大圖與 _plan.py 骨架。"),
            ("2", "填企劃", "只寫畫面看得到且有證據的字幕；TODO 必須清空。"),
            ("3", "建置", "Shorts gate → ffmpeg 成片 → LUFS／首幀／字幕對位 QA。"),
        )
        for row, (number, title, text) in enumerate(steps):
            ttk.Label(guide, text=number, style="Status.TLabel").grid(
                row=row, column=0, sticky="n", padx=(0, 10), pady=7
            )
            ttk.Label(guide, text=f"{title}\n{text}", wraplength=330).grid(
                row=row, column=1, sticky="w", pady=7
            )

    def _build_tools_tab(self, notebook) -> None:
        ttk = self.ttk
        tab = ttk.Frame(notebook, padding=16)
        notebook.add(tab, text="影片工具")
        tab.columnconfigure(0, weight=1)

        teardown = ttk.LabelFrame(tab, text="競品節奏量測", padding=11)
        teardown.grid(row=0, column=0, sticky="ew", pady=(0, 9))
        teardown.columnconfigure(1, weight=1)
        self._path_row(teardown, 0, "影片／資料夾", self.teardown_target_var, self._browse_teardown)
        ttk.Label(teardown, text="字幕區域").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Combobox(
            teardown,
            textvariable=self.band_var,
            values=("wide", "top", "mid", "bottom"),
            state="readonly",
            width=12,
        ).grid(row=1, column=1, sticky="w")
        ttk.Label(teardown, text="切鏡門檻").grid(row=1, column=1, sticky="e", padx=(0, 130))
        ttk.Entry(teardown, textvariable=self.threshold_var, width=10).grid(
            row=1, column=1, sticky="e", padx=(0, 30)
        )
        self._run_button(teardown, "開始量測", self.start_teardown).grid(
            row=1, column=2, sticky="e"
        )

        qa = ttk.LabelFrame(tab, text="交付 QA", padding=11)
        qa.grid(row=1, column=0, sticky="ew", pady=(0, 9))
        qa.columnconfigure(1, weight=1)
        self._path_row(qa, 0, "成片", self.qa_video_var, self._browse_qa_video)
        ttk.Checkbutton(
            qa,
            text="檢查音訊（LUFS／尾端靜音／A-V 同步）",
            variable=self.qa_audio_var,
        ).grid(row=1, column=1, sticky="w", pady=4)
        self._run_button(qa, "執行交付 QA", self.start_delivery_qa).grid(
            row=1, column=2, sticky="e"
        )

        cleaner = ttk.LabelFrame(tab, text="螢幕錄影清理（M104）", padding=11)
        cleaner.grid(row=2, column=0, sticky="ew")
        cleaner.columnconfigure(1, weight=1)
        self._path_row(cleaner, 0, "原始錄影", self.clean_source_var, self._browse_clean_source)
        self._path_row(
            cleaner,
            1,
            "輸出 MP4",
            self.clean_output_var,
            self._browse_clean_output,
            save=True,
        )
        ttk.Label(cleaner, text="裁切 W:H:X:Y").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Entry(cleaner, textvariable=self.crop_var, width=22).grid(row=2, column=1, sticky="w")
        small = ttk.Frame(cleaner)
        small.grid(row=2, column=1, sticky="e")
        ttk.Label(small, text="頭").pack(side="left")
        ttk.Entry(small, textvariable=self.head_trim_var, width=7).pack(side="left", padx=(4, 10))
        ttk.Label(small, text="尾").pack(side="left")
        ttk.Entry(small, textvariable=self.tail_trim_var, width=7).pack(side="left", padx=(4, 0))
        ttk.Label(cleaner, text="秒（頭尾各至少 1 秒）", style="Hint.TLabel").grid(
            row=2, column=2, sticky="w", padx=(8, 0)
        )
        self._run_button(cleaner, "開始清理", self.start_screen_clean).grid(
            row=3, column=2, sticky="e", pady=(8, 0)
        )

    def _build_health_tab(self, notebook) -> None:
        ttk = self.ttk
        tab = ttk.Frame(notebook, padding=18)
        notebook.add(tab, text="環境與說明")
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)
        toolbar = ttk.Frame(tab)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ttk.Label(
            toolbar,
            text="可攜 EXE 會內嵌 numpy、Pillow、ffmpeg 與 ffprobe；OCR 維持選配。",
            style="Hint.TLabel",
        ).pack(side="left")
        self._run_button(toolbar, "重新檢查", self.refresh_dependencies).pack(side="right")
        columns = ("component", "status", "version", "path")
        self.health_tree = ttk.Treeview(tab, columns=columns, show="headings", height=8)
        headings = {"component": "元件", "status": "狀態", "version": "版本", "path": "來源"}
        widths = {"component": 110, "status": 80, "version": 360, "path": 520}
        for column in columns:
            self.health_tree.heading(column, text=headings[column])
            self.health_tree.column(column, width=widths[column], anchor="w")
        self.health_tree.grid(row=1, column=0, sticky="nsew")
        note = (
            "使用邊界：Path 1 不需要 CapCut；所有素材、企劃與輸出留在你選擇的本機資料夾。\n"
            "Shorts 掃描只產生企劃骨架，不會替你編造品名、價格或畫面事實。"
            "交付 QA 產生的全幀圖仍須人工逐張確認。"
        )
        ttk.Label(tab, text=note, wraplength=1020, justify="left").grid(
            row=2, column=0, sticky="w", pady=(14, 0)
        )

    def _path_row(self, parent, row, label, variable, command, save=False) -> None:
        self.ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=5)
        self.ttk.Entry(parent, textvariable=variable).grid(
            row=row, column=1, sticky="ew", padx=(10, 8), pady=5
        )
        self.ttk.Button(parent, text="另存…" if save else "瀏覽…", command=command).grid(
            row=row, column=2, sticky="e", pady=5
        )

    def _run_button(self, parent, text, command, primary=False):
        button = self.ttk.Button(
            parent,
            text=text,
            command=command,
            style="Primary.TButton" if primary else "TButton",
        )
        self.run_buttons.append(button)
        return button

    def _browse_project(self) -> None:
        self._choose_directory(self.project_var, "選擇 Shorts 專案資料夾")

    def _browse_bgm(self) -> None:
        self._choose_directory(self.bgm_var, "選擇 BGM 素材庫")

    def _browse_teardown(self) -> None:
        from tkinter import filedialog

        path = filedialog.askopenfilename(
            title="選擇競品 MP4（取消後可直接貼入資料夾路徑）",
            filetypes=[("MP4 video", "*.mp4"), ("All files", "*.*")],
        )
        if path:
            self.teardown_target_var.set(path)

    def _browse_qa_video(self) -> None:
        self._choose_video(self.qa_video_var, "選擇要驗收的成片")

    def _browse_clean_source(self) -> None:
        self._choose_video(self.clean_source_var, "選擇原始螢幕錄影")
        if self.clean_source_var.get() and not self.clean_output_var.get():
            source = Path(self.clean_source_var.get())
            self.clean_output_var.set(str(source.with_name(f"{source.stem}-clean.mp4")))

    def _browse_clean_output(self) -> None:
        from tkinter import filedialog

        path = filedialog.asksaveasfilename(
            title="清理後輸出",
            defaultextension=".mp4",
            filetypes=[("MP4 video", "*.mp4")],
        )
        if path:
            self.clean_output_var.set(path)

    def _choose_directory(self, variable, title: str) -> None:
        from tkinter import filedialog

        path = filedialog.askdirectory(title=title, initialdir=variable.get() or None)
        if path:
            variable.set(path)

    def _choose_video(self, variable, title: str) -> None:
        from tkinter import filedialog

        path = filedialog.askopenfilename(
            title=title,
            filetypes=[("Video", "*.mp4 *.mov *.mkv"), ("All files", "*.*")],
        )
        if path:
            variable.set(path)

    def _settings_payload(self) -> dict:
        return {
            "project_dir": self.project_var.get(),
            "bgm_dir": self.bgm_var.get(),
            "teardown_target": self.teardown_target_var.get(),
            "band": self.band_var.get(),
            "threshold": self.threshold_var.get(),
            "qa_video": self.qa_video_var.get(),
            "qa_audio": self.qa_audio_var.get(),
            "clean_source": self.clean_source_var.get(),
            "clean_output": self.clean_output_var.get(),
            "crop": self.crop_var.get(),
            "head_trim": self.head_trim_var.get(),
            "tail_trim": self.tail_trim_var.get(),
        }

    def _save_settings(self) -> None:
        try:
            save_settings(self._settings_payload())
        except OSError as exc:
            self._append_log(f"[WARN] 設定未儲存：{exc}\n")

    def start_short(self, action: str) -> None:
        label = WORKFLOWS[f"shorts_{action}"]
        self._save_settings()
        self._run_async(
            label,
            lambda: run_short_job(
                action,
                self.project_var.get(),
                self.bgm_var.get(),
            ),
        )

    def start_teardown(self) -> None:
        try:
            target, band, threshold = parse_teardown_options(
                self.teardown_target_var.get(), self.band_var.get(), self.threshold_var.get()
            )
        except ValueError as exc:
            self._show_error(str(exc))
            return
        self._save_settings()
        self._run_async(
            WORKFLOWS["teardown"],
            lambda: run_teardown_job(target, band, threshold),
        )

    def start_delivery_qa(self) -> None:
        self._save_settings()
        self._run_async(
            WORKFLOWS["delivery_qa"],
            lambda: run_delivery_qa_job(
                self.qa_video_var.get(), check_audio=self.qa_audio_var.get()
            ),
        )

    def start_screen_clean(self) -> None:
        try:
            parsed = parse_screen_clean_options(
                self.clean_source_var.get(),
                self.clean_output_var.get(),
                self.crop_var.get(),
                self.head_trim_var.get(),
                self.tail_trim_var.get(),
            )
        except ValueError as exc:
            self._show_error(str(exc))
            return
        self._save_settings()
        self._run_async(
            WORKFLOWS["screen_clean"],
            lambda: run_screen_clean_job(*parsed),
        )

    def refresh_dependencies(self) -> None:
        def check() -> OperationResult:
            status = dependency_status()
            return OperationResult(
                all(item["ok"] for item in status.values()),
                "依賴檢查完成。",
                details=status,
            )

        self._run_async(
            WORKFLOWS["health"],
            check,
            quiet=True,
        )

    def _run_async(self, label: str, callback: Callable[[], OperationResult], quiet=False) -> None:
        if self.running:
            self._show_error("目前已有工作執行中，請等它完成。")
            return
        self.running = True
        self.status_var.set(f"執行中：{label}")
        for button in self.run_buttons:
            button.configure(state="disabled")
        if not quiet:
            self._append_log(f"\n==> {label}\n")

        def worker() -> None:
            writer = QueueWriter(self.events)
            try:
                with contextlib.redirect_stdout(writer), contextlib.redirect_stderr(writer):
                    result = callback()
            except Exception as exc:  # noqa: BLE001 - GUI boundary reports all failures
                self.events.put(("error", (label, str(exc), traceback.format_exc())))
            else:
                self.events.put(("result", (label, result)))

        threading.Thread(target=worker, name=f"path1-{label}", daemon=True).start()

    def _poll_events(self) -> None:
        try:
            while True:
                kind, payload = self.events.get_nowait()
                if kind == "log":
                    self._append_log(payload)
                elif kind == "error":
                    label, message, trace = payload
                    self._append_log(f"\n[ERROR] {label}: {message}\n{trace}\n")
                    self._finish(False, f"失敗：{label}")
                    self._show_error(message)
                elif kind == "result":
                    label, result = payload
                    self._handle_result(label, result)
        except queue.Empty:
            pass
        self.root.after(80, self._poll_events)

    def _handle_result(self, label: str, result: OperationResult) -> None:
        self.last_output = result.output_dir
        self._append_log(f"\n[{'GREEN' if result.ok else 'BLOCKED'}] {result.message}\n")
        if label == WORKFLOWS["health"]:
            self._render_health(result.details)
        self._finish(result.ok, result.message)

    def _finish(self, ok: bool, status: str) -> None:
        self.running = False
        self.status_var.set(("完成：" if ok else "需要處理：") + status)
        for button in self.run_buttons:
            button.configure(state="normal")

    def _render_health(self, status) -> None:
        for item in self.health_tree.get_children():
            self.health_tree.delete(item)
        for name, info in status.items():
            self.health_tree.insert(
                "",
                "end",
                values=(
                    name,
                    "可用" if info["ok"] else "缺少",
                    info["version"],
                    info["path"],
                ),
            )
        good = sum(1 for info in status.values() if info["ok"])
        self.dependency_var.set(f"核心依賴 {good}/{len(status)} 可用")

    def _append_log(self, text: str) -> None:
        self.log.insert("end", text)
        self.log.see("end")

    def _show_error(self, message: str) -> None:
        from tkinter import messagebox

        messagebox.showerror("Path 1 工作台", message, parent=self.root)

    def show_about(self) -> None:
        from tkinter import messagebox

        messagebox.showinfo(
            "關於",
            f"video-autopilot-kit Path 1 工作台 v{APP_VERSION}\n\n"
            "Windows-first、免 CapCut、所有素材留在本機。\n"
            "保留 Hao0321 原專案與 MIT 授權標示。",
            parent=self.root,
        )

    def open_plan(self) -> None:
        project = Path(self.project_var.get().strip().strip('"'))
        self._open_path(project / "_plan.py", "找不到 _plan.py；請先掃描素材。")

    def open_short_output(self) -> None:
        project = Path(self.project_var.get().strip().strip('"'))
        self._open_path(project / "_out", "還沒有輸出資料夾。")

    def open_last_output(self) -> None:
        if not self.last_output:
            self._show_error("本次尚無輸出資料夾。")
            return
        self._open_path(self.last_output, "輸出路徑不存在。")

    def _open_path(self, path: Path, error: str) -> None:
        path = path.expanduser().resolve()
        if not path.exists():
            self._show_error(error)
            return
        try:
            if sys.platform == "win32":
                os.startfile(str(path))  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
        except OSError as exc:
            self._show_error(f"無法開啟：{exc}")

    def export_log(self) -> None:
        from tkinter import filedialog

        path = filedialog.asksaveasfilename(
            title="匯出執行日誌",
            defaultextension=".txt",
            filetypes=[("Text", "*.txt")],
        )
        if path:
            Path(path).write_text(self.log.get("1.0", "end-1c"), encoding="utf-8")

    def close(self) -> None:
        self._save_settings()
        self.root.destroy()


def launch(*, smoke_test: bool = False) -> int:
    try:
        import tkinter as tk
    except ImportError:
        return 2
    root = tk.Tk()
    app = Path1GUI(root)
    if smoke_test:
        root.update_idletasks()
        if app.notebook.index("end") != 3:
            root.destroy()
            return 1
        root.after(250, root.destroy)
    root.mainloop()
    return 0


def write_diagnostics(path: Path) -> int:
    """供封裝後 smoke 使用：把 EXE 實際解析到的依賴寫成 JSON。"""

    status = dependency_status()
    payload = {"app_version": APP_VERSION, "dependencies": status}
    target = Path(path).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0 if all(item["ok"] for item in status.values()) else 1


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="video-autopilot-kit Path 1 GUI")
    parser.add_argument("--smoke-test", action="store_true", help="建立 UI 後自動關閉")
    parser.add_argument("--diagnose-file", type=Path, help="寫出封裝依賴診斷 JSON 後離開")
    args = parser.parse_args(argv)
    if args.diagnose_file:
        return write_diagnostics(args.diagnose_file)
    return launch(smoke_test=args.smoke_test)


if __name__ == "__main__":
    raise SystemExit(main())
