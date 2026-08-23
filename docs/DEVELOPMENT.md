# 開發與驗證（Windows-first）

SanHsien fork 的主要開發、除錯與完整驗收環境是 Windows 11 + PowerShell。Programmatic
路徑仍保留 Linux/macOS 相容性，但新修正必須先通過 Windows canonical gate，再由 Ubuntu CI
補跨平台證據。

## Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements-dev.txt
```

核心 gate、企劃與多數 QA 不需第三方執行期套件。需要 programmatic video 或 OCR 時才安裝：

```powershell
.venv\Scripts\python -m pip install -r requirements-optional.txt
winget install ffmpeg
```

只開發 Path 1 GUI／EXE 時，依賴分層如下：

```powershell
# GUI runtime：NumPy + Pillow
.venv\Scripts\python -m pip install -r requirements-path1.txt

# EXE build：上列 runtime + PyInstaller
.venv\Scripts\python -m pip install -r requirements-build.txt
```

安裝後確認：

```powershell
ffmpeg -version
ffprobe -version
```

## 提交前驗證

預設跑完整 Windows 閘門（compile、Ruff、pytest、真 ffmpeg health）：

```powershell
pwsh -NoProfile -File tools\dev_check.ps1
```

GUI／打包相關修改另跑聚焦測試、覆蓋率與 source smoke：

```powershell
.venv\Scripts\python -m pytest -q tests\test_path1_core.py tests\test_path1_gui.py tests\test_build_exe.py
.venv\Scripts\python -m coverage erase
.venv\Scripts\python -m coverage run --branch --source=path1_core -m pytest -q tests\test_path1_core.py
.venv\Scripts\python -m coverage report --include="*path1_core.py" --fail-under=80
.venv\Scripts\python path1_gui.py --smoke-test
```

## Windows EXE 建置與 smoke

建置腳本沿用 `yt_fetch` 的「薄層 Tkinter GUI + PyInstaller spec + 一鍵 build」方式，但 Path 1
需要 ffprobe，因此 `ffmpeg.exe`、`ffprobe.exe` 兩者都必須封裝：

```powershell
.venv\Scripts\python build_exe.py
```

`build_exe.py` 會 fail-closed 檢查兩支 binary、原 distribution 的 `LICENSE`／`README.txt`，
並拒絕 `--enable-nonfree` build。完整輸出、診斷命令與實機驗收清冊見
[`PATH1_GUI.md`](PATH1_GUI.md)。修改 `path1_gui.py`、`path1_core.py`、spec 或 build script 後，
不可只以 pytest 宣稱完成；至少要重新建置 EXE，再跑 `--diagnose-file` 與 `--smoke-test`。

只改文件或需要快速迭代時可先跑 `-Quick`；提交前仍要回到完整閘門：

```powershell
pwsh -NoProfile -File tools\dev_check.ps1 -Quick
```

先跑快速閉環：

```powershell
.venv\Scripts\python -m pytest -q
.venv\Scripts\python -m ruff check tests tools
.venv\Scripts\python src\system_health.py --quick
```

修改 ffmpeg、字幕、交付 QA 或影像流程時再跑完整健康檢查：

```powershell
.venv\Scripts\python src\system_health.py
```

公開 quickstart 是相容性契約，至少確認：

```powershell
.venv\Scripts\python examples\04_shorts_gate.py
.venv\Scripts\python examples\05_interview_plan.py
.venv\Scripts\python examples\06_teardown.py
```

## 本機資料

`profiles/`、`config.py`、媒體、逐字稿、CapCut 草稿、`examples/out/`、`videos/` 與各種
planning/output 目錄不得提交。示範敏感流程時使用合成或已公開素材，並只保留最小驗證證據。

## CI 對齊

GitHub Actions 會在 Ubuntu/Python 3.9 與 Windows/Python 3.14 安裝 ffmpeg、numpy、Pillow。
Windows job 直接執行 `tools/dev_check.ps1` 的完整閘門；Ubuntu job 執行等價的 compile、Ruff、
pytest 與 full health，保留跨平台相容性證據。CodeQL 每週掃描 Python。

## 上游同步

開始同步前先讀 [`UPSTREAM.md`](UPSTREAM.md)，並執行：

```powershell
git fetch upstream main
.venv\Scripts\python tools\check_upstream_updates.py --strict
```

不得直接以 upstream 覆蓋 fork；先逐筆判斷與本 fork 修正、文件和測試是否衝突。
