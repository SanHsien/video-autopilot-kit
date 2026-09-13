# 維護決策

## 2026-08-31：v0.23.0 release bundle 不採用；watermark 維持

**決定**：不合併 `1ec32f4` 或 `b74b3be`，`reviewed_through` 維持 `6dc9ad8`。

**理由**：兩個 release commit 合計跨 178 個檔案，且仍把 release identity 指向 `Hao0321`，
並含私人品牌內容；直接採用會違反公開 fork 與本 fork Path 1/CapCut 契約。這是有界審查，
不是把其後 10 個 updater/release commits 視為已審。

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

## 2026-08-29：上游檢查補上 PR 與 issue 兩個面向

**決定**：`check_upstream_updates.py` 補上以 `--state all` 收集上游 PR／issue 的邏輯，
`upstream-check.yml` 補 `GH_TOKEN: ${{ github.token }}`，新增 `tests/test_upstream_updates.py`。
Baseline 既有的水位不動。

**理由**：`docs/UPSTREAM.md` 早就寫著「四個面向都要看」，`upstream_baseline.json` 也記著
`reviewed_pr_through` 與 `reviewed_issue_through`——但**沒有任何程式讀那兩個欄位**，檢查器只比對
commit 水位。那兩個面向不是「查過沒發現」，是根本沒查，而每週的排程報告長得跟查過一樣綠。
這是艦隊層級的問題：24 個 fork 裡 21 個都這樣（`SanHsien/repo-fleet-ops` 的 `docs/INCIDENTS.md`
第十條）。參考實作是 `SanHsien/harness-guard`。

三個性質，缺一不可：

- **`--state all`**：只查 `open` 看不到「開了又關、沒有合併」的 PR，而那正是「上游拒收、但可能對
  本 fork 有價值」的一類——已合併的遲早會經由 commit 抵達，被關掉的永遠不會。
- **`gh` 失敗時回 `None` 不回 `[]`**，報告寫 `Not checked` 並 **fail closed**（exit 2）。
  「沒查到」和「沒有」在綠色報告裡長得一樣，只有一個是真的。
- **`GH_TOKEN`**：`gh` 在 Actions 裡沒有憑證就列舉不到，配上 fail closed 會讓紅燈的意思變成
  「檢查器壞了」而不是「上游有東西」。

**證據**：落地後實跑 `python tools/check_upstream_updates.py`，三個面向都印出水位與待辦數；
本 repo 的 gate 全綠。

**已知代價**：水位以上真的有東西時，每週的 upstream-check 會回 exit 1。那是它該做的事——先前的
綠燈不是「沒有待辦」，是沒有人看。

**觸發條件**：報告列出項目時逐筆讀 diff、把採用／略過理由寫進本檔，然後才推進 baseline 的水位。


## 2026-08-30：上游 21 個 commit 的分類審視（未推進 commit 水位）

先前對這個 repo 的常設略過理由是「共用模組仍帶私人識別字串，本 fork 是公開 repo」，
觸發條件寫的是「上游清乾淨」。本輪實查該條件與 21 個新 commit。

### 觸發條件：仍未成立，但範圍已縮小

上游 tip 仍帶 `Hao0321`（11 檔）與「馬來西亞」（2 檔）。**但落在 `src/` 的只剩三個檔案**，
而且**本 fork 一個都沒有**：

| 上游檔案 | 本 fork |
| --- | --- |
| `src/release_manager.py` | 無 |
| `src/silent_vlog_maker/checklists.py` | 無（上游在 `6cf5681` 新增） |
| `src/silent_vlog_maker/routing.py` | 無（同上） |

其餘命中在 `LICENSE`／`README`／`examples/README.md` 等**作者署名**處——那是應該留著的，
不是外洩。所以「私人識別字串」已經不再是擋住整批引用的理由，真正擋住的是下面那條。

### 不引用：Editkin v4 轉向（`6cf5681`、`23f87b6`、`59bb9f7` 及其後續）

`6cf5681` **整個刪掉 `src/capcut_helpers/`**（−3549 行，19 個檔案，本 fork 有 2 份測試覆蓋），
把唯一的剪輯執行路徑換成 Editkin v4。上游 `SETUP.md` 自己寫：「這個 kit 只有一條現行剪輯執行
路徑：**Editkin v4 structured workflow**」「使用 Editkin 支援的 **client/server 環境**」。

也就是說引用它等於：刪掉本 fork 現在能跑的 CapCut 工具鏈，換成一個**需要外部 client/server
環境**、而本 fork 沒有也不打包的執行期。這不是「產品方向不同」這種空話——是本線引用之後會失去
可執行能力、且換不到可執行的替代品。

**觸發條件**：本 fork 決定引進 Editkin 環境，或上游恢復第二套 editor runtime。

### 不引用：發佈中樞與 release 打包（`62f44e6`／`0f9c367`／`9252d89`／`1c660a8` 等）

這些改的是上游的發佈側：`publish_hub.py`、`autonomy_standard`、`remix_planner`、
`release_manager.py`。**本 fork 一個都沒有**（`git ls-files | grep -E "publish_hub|autonomy_standard|remix_planner"` 0 命中）。
例如 `0f9c367`「prevent withdrawn renders from resurfacing」全在 `src/publish_hub.py`。

與本 fork 重疊的部分只有 `.github/workflows/ci.yml`、`README*`、`SETUP*`、`CHANGELOG.md`
——**這四類本 fork 都有自己的版本**（Windows/Ubuntu CI、fork 文件），上游的改動不適用。

### 不引用：`4f46728` 的 `platform_compat.py`

看起來像跨平台修正，實際只動 `_mac_font_candidates()`：調整 macOS 的 PingFang／Hiragino／
STHeiti 探測順序。本 fork 是 **Windows-first**，這段在 Windows 路徑上不會執行。

### 不引用：`cf60b58`／`23f87b6` 的 `system_health.py`

兩筆都只是往 `REQUIRED` 檔案清單追加項目，追加的全是上游才有的模組
（`workflow_contract.py`、`publish_hub.py`、`tools/code-cleanup-helper/`、
`battle_plan_components.py`）。引用會讓本 fork 的健康檢查去要求一批這裡不存在的檔案，
把一個好用的檢查變成永遠紅燈。

### 仍待審：`1ec32f4`（13 個 fork 檔）與 `b74b3be`（43 個 fork 檔）

v0.23.0 的兩個 release commit 動到本 fork 也有的產品檔（`shorts_gate.py`、`shorts_autopilot.py`、
`silent_vlog_maker/` 多個模組、`longform_maker/word_captions.py`）。**這兩筆的 diff 還沒逐行讀**，
所以 **commit 水位不推進**——推進等於宣稱審過，而事實不是。

PR 水位 13 → 14（`#14` 是 v0.23.0 的 release PR，內容即上述 commit，結論同上）；
issue 水位維持 0（實查上游 issue 數為 0）。

**下一步**：只讀 `1ec32f4` 與 `b74b3be` 對那 13／43 個檔的 diff，判斷哪些是與 Editkin 無關的
獨立修正（那些可以引用），哪些是轉向的一部分（跟著上面的結論走）。做完才推進 commit 水位。
