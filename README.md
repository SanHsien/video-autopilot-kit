# 🎬 video-autopilot-kit

> **Windows-first 維護型 fork：把影片製作方法論、ffmpeg 自動化、CapCut 輔助流程與機械化 QA gate，整理成可自行填入資料的本機工具箱。**

[English](README.en.md)

本 repo fork 自 [`Hao0321/video-autopilot-kit`](https://github.com/Hao0321/video-autopilot-kit)，沿用 MIT License 與完整 Git 歷史。上游提供核心影片自動化框架與知識庫；這個 fork 的重點是讓它在 **Windows 11 + PowerShell** 上更容易開發、驗證與實際使用。

## 這個 fork 額外提供什麼？

相較共同祖先，本維護線加入／強化了：

- **Windows-first 開發與驗收**：可重現的 venv、PowerShell 一鍵 gate、Windows-specific regression tests。
- **Path 1 桌面工作台**：Tkinter GUI 包住既有 Programmatic 核心，不把剪輯規則重寫在 UI 裡。
- **可攜 Windows EXE**：PyInstaller 單檔建置，可內嵌 `ffmpeg`、`ffprobe`、NumPy、Pillow，建置時缺依賴會 fail-closed。
- **Windows + Ubuntu CI**：Windows 跑完整開發 gate 與 EXE build/smoke test；Ubuntu 補跨平台相容性。
- **CodeQL、Dependabot、upstream tracking**：上游更新逐筆審查，不盲目覆蓋 fork 修正。
- **Windows 可靠性修補**：包含 CapCut 原子寫入、程序關閉、UTF-8/CJK subprocess 與 optimized mode guard 等回歸保護。

完整 fork 邊界見 [`FORK.md`](FORK.md)；上游同步策略見 [`docs/UPSTREAM.md`](docs/UPSTREAM.md)。

## 你該走哪條路？

| 需求 | 建議路徑 |
|---|---|
| Mac / Linux、不要 GUI、要純程式自動化 | **Path 1 Programmatic** |
| Windows、想用桌面工作台 | **Path 1 GUI** |
| 需要 CapCut 特效、花字或既有模板 | **Path 2 CapCut-assisted** |
| 只想先驗證方法，不想準備真素材 | `examples/` demos |

> CapCut-assisted 路線屬於 **版本敏感整合**。開始前先看 [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) 的相容性說明。

## 60 秒看它跑

不需要真實影片或私人資料，也可以先跑自包含範例：

```bash
python examples/01_vertical_short.py
python examples/04_shorts_gate.py
python examples/05_interview_plan.py
python examples/06_teardown.py
```

- `01`：合成素材 → 1080×1920 直式短片。
- `04`：Shorts gate，示範壞剪法被擋、規則修正後放行。
- `05`：訪談 gate，沒來源的來賓數據在錄影前被擋下。
- `06`：競品節奏拆解與可比較指標。

Python 需求為 **3.9+**。部分純 Python gate 不需要 ffmpeg；影音合成流程則需要 `ffmpeg` / `ffprobe`。完整範例見 [`examples/README.md`](examples/README.md)。

## Windows Path 1 GUI

建立開發環境後：

```powershell
.venv\Scripts\python path1_gui.py
```

桌面工作台涵蓋主要 Programmatic 流程，包括：

- Shorts `scan → 填企劃 → build + QA`
- 競品節奏量測
- 交付 QA
- 螢幕錄影清理
- ffmpeg / ffprobe / NumPy / Pillow 依賴健檢

長時間影音工作在背景執行，素材、企劃與輸出留在使用者選擇的本機資料夾。

### 建置可攜 EXE

```powershell
.venv\Scripts\python -m pip install -r requirements-build.txt
.venv\Scripts\python build_exe.py
# dist\video-autopilot-path1.exe
```

建置會驗證必要依賴；完整 GUI、封裝與第三方授權邊界見：

- [`docs/PATH1_GUI.md`](docs/PATH1_GUI.md)
- [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)

## 核心能力

這不是單一「自動剪片腳本」，而是一組可組合的流程與 gate：

- **教學／長片**：腳本、企劃、交付 QA 與可重用的長片模組。
- **Shorts / Reels 類直式影片**：scan、企劃、build、平台感知 gate 與 QA。
- **線上訪談**：邀請、來賓研究、企劃文件與來源檢查。
- **競品拆解**：剪點、節奏、換句、音量等量測；OCR 為選配。
- **Channel ops**：追蹤與 system-health 工具。
- **CapCut helpers**：Windows-first 的草稿、程序與 post-export 輔助流程。

深入方法論與知識庫仍由上游專案持續演進；本 fork 不把上游研究內容重新包裝成 SanHsien 原創成果。

## 資料與隱私邊界

這個 repo **不應包含任何人的私人頻道資料或素材**：

- `profiles/`、`config.py` 與個人設定留在本機並由 Git 忽略。
- 不提交影片、音訊、逐字稿、CapCut 草稿、API key、cookie 或帳號資料。
- `knowledge/` 中提到第三方創作者／頻道時，只使用公開資訊，採 **citation-first：沒來源連結就不給數字**。
- KPI、voice 詞表與社群欄位應是空白模板、占位字或明確標示的範例值。
- OCR 信心分數不是品名、價格、材質或數量的真實性證據；高風險字幕仍需人工或來源佐證。
- 外部轉錄／AI 服務若被採用，資料處理由該服務自己的政策決定；本 repo 不替第三方做隱私保證。

## 開發與驗證

主要驗收環境：**Windows 11 + PowerShell**。

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements-dev.txt
pwsh -NoProfile -File tools\dev_check.ps1
```

CI 會額外驗證：

- Ubuntu / Python 3.9：compile、Ruff、pytest、system health。
- Windows / Python 3.14：完整開發 gate。
- Windows：實際 build `video-autopilot-path1.exe`，再驗證 GUI 啟動與內嵌 `ffmpeg` / `ffprobe` / NumPy / Pillow。
- CodeQL：Python security analysis。

開發細節見 [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md)。

## 文件地圖

| 目的 | 文件 |
|---|---|
| 第一次設定 | [`SETUP.md`](SETUP.md) |
| 常見問題 / CapCut 相容性 | [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) |
| Fork 差異 | [`FORK.md`](FORK.md) |
| 上游同步 | [`docs/UPSTREAM.md`](docs/UPSTREAM.md) |
| 開發與驗證 | [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) |
| Path 1 GUI / EXE | [`docs/PATH1_GUI.md`](docs/PATH1_GUI.md) |
| 外部服務整合 | [`docs/INTEGRATIONS.md`](docs/INTEGRATIONS.md) |
| Fork 專屬決策 | [`docs/DECISIONS.md`](docs/DECISIONS.md) |
| 版本歷史 | [`CHANGELOG.md`](CHANGELOG.md) |
| 最近 repo review | [`REPO_REVIEW.md`](REPO_REVIEW.md) |

## 上游與授權

- Upstream：[`Hao0321/video-autopilot-kit`](https://github.com/Hao0321/video-autopilot-kit)
- Maintained fork：[`SanHsien/video-autopilot-kit`](https://github.com/SanHsien/video-autopilot-kit)
- License：MIT

上游可能比本 fork 更新；同步前先執行 `python tools/check_upstream_updates.py`，逐筆評估再 merge / cherry-pick。fork 的價值在於 **Windows-first 採用、驗證與維護差異**，不是把上游成果重新署名。
