# 維護決策

## 2026-08-09：Path 1 GUI 採薄層 Tkinter + 可攜單檔 EXE

**決定**：以 `path1_core.py` 接回既有 Programmatic pipeline，`path1_gui.py` 只處理表單、
背景 thread、日誌與本機設定；Windows 版本用 PyInstaller 打成單檔 EXE，內嵌 NumPy、Pillow、
ffmpeg 與 ffprobe。OCR 保持選配，不進基礎 EXE。

**理由**：`yt_fetch` 已證明「薄層 Tkinter + 共用核心 + PyInstaller」符合使用者的 Windows
local-first 習慣。Path 1 的價值是既有可重現剪輯與 QA，不應為 GUI 重寫一份規則；影音工作若在
Tk 主執行緒同步執行又會造成介面假死。單檔 EXE 讓非 Python 使用者可直接使用，但仍須保留
ffmpeg/ffprobe 的版本與授權證據。

**限制**：GUI 的 Shorts scan 只生成 `_plan.py` 骨架，不替人編造畫面事實；交付 QA 的全幀圖
仍需人工查看。FFmpeg build 若缺授權/readme、缺 ffprobe 或含 `--enable-nonfree`，封裝直接停止。

## 2026-08-09：上游 PR #1／#2 不重複合併

**決定**：不 cherry-pick／merge 上游 PR #1 與 #2；兩者標記為已被 v0.12 後續實作
supersede，評估證據記在 [`UPSTREAM.md`](UPSTREAM.md)。

**理由**：兩個 PR 共同修的 `Path` import crash 已由現行函式內 lazy import 解決；PR #1 的
私人 keyword map 也已演進成中性的 `EXAMPLE_KEYWORD_MAP` 與 zero-config filename matching，
列出的私人 identifier 全數不存在。PR #1 對現行 upstream 已衝突，PR #2 套用後只會留下重複
global import，沒有新增行為或測試價值。

## 2026-08-09：Windows-first 是主要驗收契約

**決定**：Windows 11 + PowerShell 作為主要開發、除錯與完整驗收環境；提交前以
`tools/dev_check.ps1` 為 canonical gate。Programmatic path 仍維持 Linux/macOS 相容性，
由 Ubuntu CI 提供第二平台證據，但不能取代 Windows full health。

**理由**：本 fork 的差異集中在 CapCut Desktop、PowerShell 程序控制、CP950/UTF-8、CJK 路徑
與 Windows ffmpeg。原 CI 只在 Ubuntu 跑 full health，無法證明主要採用路徑。

## 2026-08-09：建立可追蹤的長期 fork

**決定**：fork `Hao0321/video-autopilot-kit`，保留 MIT 授權與完整歷史，以 upstream remote
持續追蹤；本 fork 聚焦可重現 Windows 開發環境、測試與採用阻塞修正。

**理由**：上游仍活躍、內容與程式工具有實用價值，但 v0.12 的文件／demo／公開 API 出現回歸，
且原 repo 缺少標準 CI、pytest 與貢獻治理骨架。直接使用會難以判斷升級是否安全。

**限制**：不把 fork 包裝成原創專案，不移除原作者標示；上游更新必須逐筆審查。

## 2026-08-09：恢復 Shorts gate 自訂校準契約

**決定**：恢復 `DEFAULT_RULES`、`merge_rules()`、`gate_shorts(spec, rules)` 與
`assert_shorts(spec, rules)`，同時保留 v0.12 的 S-R、S-P、S-Q。

**理由**：README、SETUP 與 example 04 都將 `rules=` 當公開採用契約；v0.12 移除它後，
quickstart 直接 ImportError，而且使用者無法依自己的 3–5 支影片校準。

## 2026-08-09：KIAO Voice 只列為受控人工整合

**決定**：可用非敏感短片試用其 VTT/SRT/TXT 輸出，但不 fork、不做未授權自動化，也不把它
當成 pipeline 的權威真值來源。

**理由**：目前沒有可 fork 的公開原始碼或公開 API 證據；正式隱私政策載明批次轉錄檔與逐字稿
預設保留 30 天，且可能交由第三方技術供應商處理，與首頁的簡化「不保留」說法不完全一致。

## 2026-08-09：不啟用 Dependabot 自動合併

**決定**：Dependabot 只提 PR；CI 與人工審查通過後才合併。

**理由**：本 repo 是活躍 upstream 的工具集合，選配影音/OCR 依賴與多平台行為容易受版本影響，
自動合併的收益小於回歸風險。
