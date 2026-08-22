# AGENTS.md

給 Codex 與其他自動化代理在本專案工作時的指引。

## 專案定位

這是 [`Hao0321/video-autopilot-kit`](https://github.com/Hao0321/video-autopilot-kit) 的 MIT fork。
核心價值是可自行填入資料的影片製作框架、ffmpeg 工具、CapCut 輔助工具與機械化 QA gate；
不是代管剪輯服務，也不附帶任何私人素材、品牌設定或訂閱服務。

`origin` 是 `SanHsien/video-autopilot-kit`，`upstream` 是原作者 repo。保留上游作者與授權標示，
本 fork 的維護差異記在 `FORK.md` 與 `docs/DECISIONS.md`。
主要開發與完整驗收環境是 Windows 11 + PowerShell；跨平台相容性由 Ubuntu CI 補證。

## 硬性邊界

- 不提交影片、音訊、CapCut 草稿、逐字稿、個人 profile、API key、cookie 或帳號資料。
- 不把 OCR 信心分數當成品名、價格、材質或數量的真實性證據；高風險字幕仍需人工或來源證據。
- 不繞過 CapCut、平台或第三方服務的付費與存取限制。
- 外部轉錄服務預設視為會處理敏感資料；採用前核對正式隱私政策，不只看首頁文案。
- 上游同步先跑 `python tools/check_upstream_updates.py`，逐筆審查後再 merge/cherry-pick；不盲目覆蓋 fork 修正。

## 技術與資料流

- Python 3.9+；核心 gate 可零依賴執行。
- 影片處理使用 `ffmpeg` / `ffprobe`。
- `src/longform_maker/`：腳本、企劃、Shorts 與字幕 gate。
- `src/silent_vlog_maker/`：ffmpeg 直式影片流程。
- `src/capcut_helpers/`：CapCut 草稿與交付 QA 工具。
- `src/interview_autopilot.py`：訪談企劃文件流程。
- `src/teardown.py`：競品節奏量測；OCR 為選配。
- `path1_core.py`／`path1_gui.py`：Path 1 可測 adapter 與 Tkinter 桌面工作台。
- `video_autopilot_path1.spec`／`build_exe.py`：內嵌 ffmpeg/ffprobe 的 Windows 單檔 EXE。

## 開發原則

- 修 bug 先補可重現失敗測試，再做最小修正。
- 上游公開 API、README quickstart 與 examples 視為相容性契約。
- 不為了套格式而大改上游程式；Ruff 只要求 `tests/` 與 `tools/`。
- 使用繁體中文回覆；使用者文件以繁中為主，公開入口同步維護英文摘要。
- 修改行為時同步更新 `CHANGELOG.md`、相關文件與自帶 self-test。
- GUI 保持薄層；剪輯、QA 與量測規則留在既有核心，長工作不得阻塞 Tk 主執行緒。
- EXE build 必須 fail-closed 檢查 ffmpeg/ffprobe 與授權文件，不封裝 `--enable-nonfree` build。
- **合併任何 PR 前先讀 diff**（包含 Dependabot 開的）：`gh pr diff <編號>`。CI 綠燈證明的是「測試沒紅」，不是「改了什麼、該不該進 main」——lockfile 的連鎖升級、transitive major、跨出宣告範圍的變更，只有讀 diff 看得到。核准或合併訊息要寫出讀到什麼、為什麼可接受。

## 文件責任

- `README.md` / `README.en.md` 是公開產品與 fork 入口：說明用途、SanHsien-specific 差異、快速開始與安全邊界。
- 不把每版 release notes、完整方法論或上游研究複製進 README；版本歷史放 `CHANGELOG.md`，方法論留在 `knowledge/` 與上游文件。
- Fork 差異與維護理由放 `FORK.md`；同步策略放 `docs/UPSTREAM.md`；實作與驗收細節放 `docs/DEVELOPMENT.md` / `docs/PATH1_GUI.md`。
- `REPO_REVIEW.md` 是風險快照，不是每個一般 bug 的流水帳；只有修正既有 review 項目或新問題改變風險結論時才更新。

## 常用指令

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements-dev.txt
pwsh -NoProfile -File tools\dev_check.ps1
.venv\Scripts\python -m pytest -q
.venv\Scripts\python src\system_health.py --quick
.venv\Scripts\python src\system_health.py
.venv\Scripts\python -m ruff check tests tools
.venv\Scripts\pre-commit.exe run --all-files
.venv\Scripts\python path1_gui.py --smoke-test
.venv\Scripts\python -m pip install -r requirements-build.txt
.venv\Scripts\python build_exe.py
```

## 文件入口

- 使用：`README.md`、`SETUP.md`、`TROUBLESHOOTING.md`
- Fork 關係：`FORK.md`、`docs/UPSTREAM.md`
- 開發：`docs/DEVELOPMENT.md`、`docs/PATH1_GUI.md`、`REPO_REVIEW.md`
- 決策：`docs/DECISIONS.md`
- 外部字幕整合：`docs/INTEGRATIONS.md`
- 貢獻與安全：`CONTRIBUTING.md`、`SECURITY.md`

## 對外邊界：PR 只打本 fork

- **PR、push、release 一律指向 `SanHsien/video-autopilot-kit`。** 對上游 `Hao0321/video-autopilot-kit` 開 PR、push 或發 release
  需要主人在當次對話明確同意回貢；「fork 一份」「建開發環境」「比照其他 repo」都不是同意。
- 根因是機制不是粗心：`gh` 在 fork clone 的**預設 repo 就是上游**（`gh repo set-default --view` 會回
  `Hao0321/video-autopilot-kit`），裸跑 `gh pr create` 必然打上去。每個 clone 先跑一次
  `gh repo set-default SanHsien/video-autopilot-kit`。
- 開 PR 仍明寫 `gh pr create --repo SanHsien/video-autopilot-kit --base <分支> --head <分支>`，並**讀輸出的 URL**，
  owner 必須是 `SanHsien`。不是就立刻 `gh pr close` 留言道歉說明，再對 origin 重開。
- 2026-08-22 一天內兩個工作階段各誤開一個上游 PR（`lidge-jun/opencodex#2373`、
  `hamanpaul/paulsha-cortex#787`）。批次跑多個 repo 時最容易略過確認，而那正是兩次出事的場合。

## 依賴新鮮度：紅燈的兩條正當出口

每月的依賴新鮮度檢查比對的是**宣告**與現行版。當某個下限**不該**跟著現行版走時，只有兩種
留下理由的做法：

- **維持宣告**：在宣告那一行加 `# freshness-hold: <理由>`。用於長期政策（例如矩陣還有舊
  Python、或這個下限就是我們要的）。
- **已延後**：在 `.github/dependency-deferrals.json` 加
  `{"deferredLatest": "<當時看到的版本>", "reason": "<為什麼這次不升>"}`。PyPI 一超過該版本，
  延後自動失效、報告恢復提醒——所以不會變成永久靜音。沒有 `deferredLatest` 的條目直接忽略。

**不要用調高下限的方式讓紅燈消失**：宣告是相容性承諾，不是消音鍵。
