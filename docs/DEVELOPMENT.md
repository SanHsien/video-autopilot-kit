# 開發與驗證

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

安裝後確認：

```powershell
ffmpeg -version
ffprobe -version
```

## 提交前驗證

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

GitHub Actions 會在 Ubuntu/Python 3.9 與 Windows/Python 3.14 執行 compile、Ruff、pytest 與
quick health。Ubuntu job 另裝 ffmpeg、numpy、Pillow 後跑完整 health。CodeQL 每週掃描 Python。

## 上游同步

開始同步前先讀 [`UPSTREAM.md`](UPSTREAM.md)，並執行：

```powershell
git fetch upstream main
.venv\Scripts\python tools\check_upstream_updates.py --strict
```

不得直接以 upstream 覆蓋 fork；先逐筆判斷與本 fork 修正、文件和測試是否衝突。
