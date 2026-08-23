# 維護決策

## 2026-08-23：實查 v0.21.2（PR #13），維持不引用

**決定**：`reviewed_date` 推進到 2026-08-23，`reviewed_through` 不動。上游 `release/v0.21.2`
（`62f44e6`）逐項看完，仍不引用。

**理由（三項都實查過，不是類推）**：
1. 拒絕 v0.14–v0.21.1 的主因（共用模組帶私人識別字串）在 v0.21.2 **仍然成立**：`src/` 底下
   `Hao0321` 4 檔、`馬來西亞` 6 檔、`桃園機場` 2 檔、`IMG_5998` 1 檔，專案代號 `#000`–`#006`
   散在五個檔案。本 fork 是公開 repo 且已中性化，合併等於倒退。
2. 這一版的主題（caption `chip` 種類、`persistent_label_policy: intro`）渲染端在
   `src/caption_director.py`，**本 fork 沒有這個檔案**；`src/publish_hub.py` 同樣沒有。只搬
   `shorts_gate.py` 的 25 行會讓 gate 放行本 fork 渲染不出來的字幕。
3. 逐檔確認**沒有可獨立取用的錯誤修正**：`shorts_autopilot.py` 的 +186 行是新功能
   （editorial fingerprint，schema 名 `hao.editorial-fingerprint/v1`），其餘檔案跟著同一條線。

**觸發條件**：上游把 `src/` 的私人識別字串清乾淨，或本 fork 自行實作 `caption_director`
對應層。在那之前這一批不需要再評估。

## 2026-08-22：不合併上游 v0.14–v0.21.1 批次（11 commits）

**決定**：`fc4d818` 到 `6dc9ad8` 共 11 個上游提交標記為已審查、整批不合併，review
watermark 推進到 `6dc9ad8b3dc9b2ef158e4eac835f5f721e5b3bed`。watermark 只代表審查過，
不代表採用。

**理由**：這批是 216 個檔案、+42,129/-1,576 行的產品線重寫（visual director、3D、
tracked graphics、publish hub、code-cleanup-helper skill）。兩件事讓它不能整批合併、
也不能逐檔挑：

1. **會把個人／私人識別字串帶回公開 fork。** 上游看來是從作者的私人工作副本重新
   發布：本 fork 已中性化的共用模組又被改回去。實際命中——`Hao0321`／`hao0321` 7 次、
   專案代號 `#000`–`#006` 18 次、`馬來西亞` 7 次、`桃園機場` 2 次、`IMG_5998` 1 次，
   全在 `src/` 的共用檔案裡（`scene_audit.py`、`frame_audit.py`、`text_overlay.py` 等）。
2. **共用檔案的改動已綁在新架構上。** 例如 `effects.py` 的 `apply_cinematic_grade()`
   改成呼叫 `visual_master.lut_filter_for_plan()`；其他共用檔新增
   `art_direction`、`project_paths`、`publish_hub`、`editorial_templates` 等 import。
   要挑其中一支就得把整條上游產品線帶進來，而那正是本 fork 決定不走的方向。

另外 `src/system_health.py` 被上游改寫成單行 docstring 的精簡版，移掉了本 fork
TESTS／IMPORT_SANITY／CORE_FILES 三類分開報告與真 ffmpeg 測試集——那是本 fork 的
穩定性中樞，降級採用沒有理由。Path 1（本 fork 的產品：GUI 與可攜 EXE）上游完全沒碰。

**審查方式**（以便日後判斷這份結論的強度）：比對 baseline→`upstream/main` 的完整檔案
交集（28 個共用檔、約 2,600 行）、逐檔 numstat、共用檔的新增 import 掃描、私人識別字串
掃描，並實讀 `effects.py`、`system_health.py`、`scene_audit.py`、`frame_audit.py`、
`text_overlay.py` 的差異。未逐行讀完 2,600 行——結論是「整批因結構性理由不採用」，
不是「逐行確認每個改動都無價值」。

**後續採用門檻**：上游若把個人識別字串清出共用模組，或本 fork 決定引進 visual
master／publish hub 架構，屆時以當時的上游程式重新評估，不沿用本次結論。單獨想要的
能力（例如 word captions 時間軸、shorts gate 檢查）以本 fork 自己的實作補，不 cherry-pick。


## 2026-08-12：不直接合併上游 v0.13.0 updater／storage commits

**決定**：將上游 `fb1fc8f`、`f4527c4`、`0aeaf48` 標記為已審查但不直接合併；PR #3
維持 deferred。review watermark 推進到 `0aeaf48c19a7820741ccca3a4184b9d8bec816dc`，不表示程式已採用。

**理由**：本 fork 與上游都已發布不同內容的 `v0.13.0`；上游 updater/channel/Skill 指向
`Hao0321`，無法安全更新 `SanHsien` fork。正式上游 ZIP 又缺 `.gitignore`，manifest 私人路徑
掃描沒有命中仍存在的 BGM 私人預設。storage lifecycle 的 current-only 方向值得保留，但會修改
Shorts 成片命名，且目前 cleanup 在所有 fail-closed 驗證完成前就刪除中間檔。

**後續採用門檻**：若要移植，另做 fork 專用 release identity/版本遷移；source archive 將
`.gitignore` 設為 required；storage cleanup 改成 validate-first 並補失敗不刪檔、GUI/CLI 舊輸出
相容與 rollback 測試。逐項證據見 [`UPSTREAM.md`](UPSTREAM.md)。

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
