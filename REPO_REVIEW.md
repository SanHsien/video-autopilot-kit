# Repository review（Windows-first）

- Review date: 2026-10-30
- Review baseline: fork `705508a5c84aa36502e3cfe86750ea00bc68a755`
- Upstream reviewed through: `a50c73bde0c5bcb5b82e4d28f812e780e20cb1a7`
- Primary environment: Windows 11、PowerShell、Python 3.12+、ffmpeg 9
- Status: v0.13.0 Path 1 GUI／EXE 維持全綠；四個 gate 改為 fail-closed；上游 delta 已審查分流，阻擋項未帶入 fork

## 結論

這個 fork 值得繼續使用，且適合作為 Windows-first 的本機 AI 剪輯工具箱。公開的六個範例、
核心 gate 與真 ffmpeg health 都能在 Windows 執行（Windows dev check 257 passed）；本輪主要風險
不是剪輯演算法，而是 CapCut 草稿一致性、Windows 程序驗證、CP950/UTF-8 邊界與自動流程的 fail-closed 行為。

fork 現行 runtime 沒有保留未修的 high/medium finding。2026-08-09 的 Bandit medium/high 掃描
為 0，`requirements-dev.txt` 的 pip-audit 沒有已知漏洞；2026-10-26 依安全通告將 Path 1 要求升級為
`Pillow>=13`（修補 GHSA-5x8w-8jj5-q52h 等漏洞），配合 `numpy>=2.5` 確立 Path 1 需要 Python 3.12+
（零依賴 gate 仍支援 3.9+）。上游審查水位已推進至 commit `a50c73b`、PR 29、issue 30，其中阻擋直接移植
的採用條件記於 [`docs/DECISIONS.md`](docs/DECISIONS.md) 與 [`docs/UPSTREAM.md`](docs/UPSTREAM.md)，
不代表已進入 fork runtime。

## 上游審查與採用歷史（Upstream delta review）

上游在 v0.14 之後大幅轉向 Editkin 渲染、visual master、publish hub 等架構，並將私人識別字串帶回 `src/`。
本 fork 維持 Path 1（ffmpeg 影片工具 + Tkinter GUI + 可攜 EXE）方向，不整批合併上游模組；上游更新一律採取
「逐筆審查、隔離測試、最小採用」原則：

1. **2026-08-12 審查**（至 `0aeaf48`）：上游 release manager、deterministic archive 與 storage lifecycle 因合約衝突與私人路徑不予合併（PR #3 deferred）。
2. **2026-08-23 與 08-30 審查**（至 PR #14）：PR #13 與 Editkin v4 轉向等改動不引用；保留未讀 diff 的 commit 水位不盲目推進。
3. **2026-09-30 審查**（至 `b449e7a`、PR #23、issue #16）：29 個 commit 逐項分流，確認無可獨立取用修正。
4. **2026-10-25 審查與採用**（至 `a50c73b`、PR #29、issue #30）：
   - 維護者決定採用 issue #4 列出的三項改動：`TONEMAP_FILTER` `npl` 250 → 100（HDR 轉 SDR 成品不再壓暗 2.5 倍）；`plan_gate` P4（僅認真實日期、非未來、真人複核人簽章）與 `interview_gate` 型別化來源（`url:`/`file:`/`sha256:`）；`shorts_gate` 半形字元權重算 0.5 字（放寬英數混排讀速限制）。
   - 對上游 PR #25（Shorts 畸形輸入）與 PR #26（gate 缺陷），以本 fork 自己的最小修正修補（非 cherry-pick），釘住測試防止回歸。

## v0.13.0 Path 1 GUI／EXE review

本輪依 `yt_fetch` 的已驗證模式加入薄層 Tkinter GUI、可測 adapter 與 PyInstaller 單檔封裝。GUI 覆蓋 Shorts scan/build、
競品量測、交付 QA、螢幕錄影清理與依賴健檢；所有長時間影音工作都在背景 thread 執行，
剪輯與 QA 規則仍以原模組為 SoT。

| ID | 嚴重度 | Finding | 修復與證據 |
|---|---|---|---|
| G-01 | High | 原 `shorts_autopilot` 把 inbox 設為 placeholder、BGM 設為原作者私人磁碟路徑；GUI 若沿用 global 會讓一般使用者 scan/build 到錯誤位置。 | `scan()`／`build()` 接受明確 caller root；CLI fallback 改用 `VIDEO_KIT_SHORTS_INBOX`／`VIDEO_KIT_BGM_ROOT` 與中性 repo fallback；adapter 與 env contract tests。 |
| G-02 | High | 只把 Python 打成 EXE 不能證明 Path 1 可攜；現有核心同時呼叫 `ffmpeg` 和 `ffprobe`，少包其中一支仍會在使用者電腦失敗。 | spec 同時嵌入兩支 binary；封裝後 `--diagnose-file` 顯示兩者均解析自 `_MEI…\bin`，NumPy/Pillow 也在 bundle。 |
| G-03 | Medium | 在 Tk callback 直接跑 ffmpeg 會讓 UI 長時間無回應，也無法持續顯示既有 pipeline 日誌。 | 單一背景 worker + thread-safe queue；run buttons 執行中停用，stdout/stderr 串流到全域日誌，完成／BLOCKED 狀態明確。 |
| G-04 | Medium | 把 Gyan full build 封進 MIT 專案但不保存其 license/build provenance，會讓使用者誤以為 MIT 涵蓋所有內容。 | build 拒絕 `--enable-nonfree`，確認本候選為 GPL-3.0-or-later，保留 FFmpeg 原 LICENSE/README、第三方 notices 與三個 binary hash。 |
| G-05 | High | Pillow <= 12.3.0 存在重大影像解碼安全通告（如 GHSA-5x8w-8jj5-q52h 堆積溢位），而 Path 1 會開啟本機影像。 | `requirements-path1.txt` 將 Pillow 下限升至 13，連帶確立 Path 1 需 Python 3.12+（配合 `numpy>=2.5`）；零依賴核心 gate 與 CI 3.9 leg 維持不變。 |
| G-06 | Medium | `screen_clean` / Path 1 screen cleaner 若輸入 NaN/inf 剪裁或非 ASCII 數字，可能穿透 M104 隱私底線。 | 排除 NaN/inf 前後剪裁，裁切框數值前置拒絕非 ASCII 數字；以回歸測試釘住行為。 |
| G-07 | Low | `build_exe.py` 的 `app_version` 與 `path1_core.APP_VERSION` 分離，改版時可能字面值不同步。 | 補齊跨模組版本一致性測試 `test_version_literals_are_synchronized`（`2c519f3`），確保打包版本與核心一致。 |

### v0.13.0 驗收證據

- 聚焦測試：Path 1 core/GUI/build contracts 全綠；`path1_core.py` branch coverage **87%**。
- Canonical Windows gate：compile、Ruff、**66 passed**、完整 ffmpeg health 全綠。
- 合成素材 adapter smoke：實際產生 `_plan.py`、`_work/_scan.json`、`_work/SHEET.jpg`。
- GUI 畫面檢查：Shorts、影片工具、環境三分頁在 1180×820 無截斷／重疊；日誌與依賴表可讀。
- Windows EXE：`video-autopilot-path1.exe`，版本 `0.13.0`，204,383,243 bytes，SHA-256
  `f50b9cfc4252826a392bd4488f10abe704b946ec35b444e5ac57df1612a05f0a`。
- 封裝後 diagnostics 與 GUI smoke 均 exit 0；結束後無殘留 process。內嵌 NumPy 2.5.1、
  Pillow 12.3.0、Gyan FFmpeg/ffprobe 9.0。

## 已修 findings

| ID | 嚴重度 | Finding | 修復與證據 |
|---|---|---|---|
| R-01 | High | `save_draft_with_sync()` 宣稱同步 7+ 份 CapCut JSON，實際漏寫 root/timeline 的 `.bak`、`.tmp`；`verify_sync()` 又忽略這些副本，會在 stale replica 存在時誤報全綠。 | 現在同步所有既存 replica、逐檔 atomic replace，驗證涵蓋相同完整集合；`test_save_and_verify_cover_every_existing_capcut_replica`。 |
| R-02 | High | `safe_kill_then_verify()` 忽略 kill return code；PowerShell 查詢失敗或不可解析時被當成「沒在跑」，而且漏查 `CapCutHelper`。這會讓草稿在程序仍持有快取時被外部修改。 | kill/query 加 timeout、同查 `CapCut` 與 `CapCutHelper`、所有錯誤 fail-closed，kill 非 0 永不回成功；`tests/test_process_windows.py`。 |
| R-03 | High | Windows 預設 CP950，但 ffmpeg/git/Python child 常輸出 UTF-8；多個 `capture_output=True, text=True` 呼叫未指定編碼。含中文檔名時可重現 reader thread `UnicodeDecodeError`，`stderr` 甚至變 `None`。 | 所有擷取文字的 subprocess 明寫 UTF-8 + replacement error handling，並用 AST hygiene test 防回歸；`test_av_util_decodes_utf8_child_output_on_cp950_windows`。 |
| R-04 | High | `shorts_autopilot` 與 `interview_autopilot` 的正式輸入閘門使用裸 `assert`。`python -O` / `PYTHONOPTIMIZE=1` 會移除素材、TODO、模板 placeholder 檢查，壞輸入仍可能產出檔案。 | 正式流程改為明確 `FileNotFoundError` / `ValueError`；以真正的 `python -O` subprocess 測試。自測區的 assert 保留。 |
| R-05 | Medium | `gate_shorts()` 對空白、缺欄位、錯 tuple、負/零 duration、越界 caption index 等規格會 `KeyError` / `IndexError` / `ValueError`，不是 gate report。 | 新增結構驗證，壞 spec 一律回 `ok=False` 與 `SPEC ...` finding；八組 malformed spec 回歸案例。 |
| R-06 | Medium | `detect_draft_format()` 會先辨識 UTF-8 BOM，解析時卻用 `utf-8`，因此合法 Windows BOM JSON 被誤判為損毀；`load_draft()` 同樣失敗。 | 解析改為 `utf-8-sig`；BOM detect/load 回歸案例。 |
| R-07 | Medium | 同一秒內連續儲存草稿會覆蓋相同 timestamp backup，失去上一版安全網。 | backup 名稱碰撞時遞增 suffix，並保留 `copy2` metadata；rapid-save 回歸案例。 |
| R-08 | Medium | 原 Windows CI 只跑 quick health，真 ffmpeg full health 只有 Ubuntu 跑，與 Windows-first 定位不一致。 | Windows/Ubuntu 都安裝 ffmpeg、numpy、Pillow；Windows CI 執行 `tools/dev_check.ps1` 完整 gate，Ubuntu 保留等價跨平台 gate。 |
| R-09 | High | 四個 gate（`plan_gate`、`interview_gate`、`shorts_gate`、`gate_core`）對惡意或畸形輸入（None、非 dict、非 list 欄位、字串數值、NaN、缺理由等）會拋出未捕獲例外（TypeError/AttributeError）或未驗證放行。 | 全面改為 fail-closed：畸形輸入一律回報 BLOCK 或引發明確 assertion，`gate_core` 在未執行檢查時回報 RED；均補齊重現測試。 |
| R-10 | Medium | `interview_autopilot invite`：來賓姓名含雙引號或 Windows 反斜線路徑（`C:\new`）會使產出的 `_guest.py` 無法編譯或字元跳脫錯誤；`render()` 誤判 `((...))` 為未填欄位。 | `ep` 與 `name` 以 `repr()` 字面值寫入；修正 `render()` 佔位解析邏輯並附測試。 |
| R-11 | Medium | `channel_tracker.save_state` 在寫檔中斷或失敗時會截斷既有的 `channel_state.json`，導致狀態遺失。 | 改寫為寫入暫存檔再使用 `os.replace` 原子替換；附失敗中斷保護測試。 |
| R-12 | Medium | `apply_subtitle_corrections` 將置換文字當作 regex 模板，若含有反斜線會變成換行或拋出 `re.error`。 | 置換文字改為字面值插入（literal insertion），不走 regex 模板展開；附反斜線測試。 |
| R-13 | Low | `tools/check_upstream_updates.py` 在本機缺少 `gh` 或 `git` 時拋出 unhandled traceback。 | 缺少 `gh` 報告為未檢查（not checked），缺少 `git` 報告為檢查失敗，正常結束無 traceback。 |
| R-14 | Low | `effects.kenburns_*` 的 `s=W:H` 語法冒號會被 ffmpeg 視為選項結束而拒絕，且畫面比例被固定；`fx_lib.double_bloom` 直通模糊導致透明黑邊滲入暗化。 | 修正 ffmpeg filter 語法為 `WxH`，pan 隨目標長寬比適應；`double_bloom` 只對 alpha mask 模糊；補齊測試。 |

## 未修項目（觀察清單）

依據 [`docs/DECISIONS.md`](docs/DECISIONS.md) 2026-10-26 第二輪深度掃描，刻意不修、列為觀察清單的項目（均屬上游原有程式、或風險低且動及既有行為）：

1. **`interview_autopilot` 的 `ep` 直接組進路徑**：`ep` 直接組進路徑（`../` 可穿出 `PLAN_ROOT`）。目前只有本機 CLI 使用者自己能傳，不構成跨信任邊界；若日後包成服務或讓第三方餵 `ep`，再加 `[A-Za-z0-9_-]+` 驗證。
2. **`shorts_autopilot.scan` 沿用既有檔案**：見到既有的 `_work/*.mp4` 就當成正規化完成，中斷過的半成品會被沿用。要改成「寫暫存檔再改名」屬於產品行為變動，等有實際案例再做。
3. **`tools/check_dependency_freshness.py` 延後名單比對**：延後名單用 `name.lower()` 比對，`pre_commit` 與 `pre-commit` 視為不同；目前兩邊都用連字號所以無影響，改名規範化前要先決定 PEP 503 全規則。
4. **`path1_gui._poll_events` 例外處理**：若事件處理丟例外就不再重排下一輪輪詢；目前找不到可觸發的輸入，只記錄。

## 已檢查但不列為 finding

- 所有外部程序使用 argv list，沒有 `shell=True`、`os.system()`、`eval()` 或 `exec()` 注入面。
- Bandit 的 low-level B603/B607 是本機 `ffmpeg`、`ffprobe`、PowerShell 可執行檔探測；PATH 由
  操作者控制，參數沒有拼成 shell command，因此不改成硬編碼絕對路徑。
- `silent_vlog_maker.audit.audit_raw_files()` 的區域 closure 在每個 clip 迴圈內同步建立並立即消費，
  Ruff B023 不會跨 iteration 延後執行，屬誤報。
- `silent_vlog_maker.helpers` 是相容用 re-export facade；其 F401 是公開 API，不可自動刪除。
- `src/` 內大量 assert 位於 `__main__` self-test；它們不是 production guard，保留可讀性。
- PLAYBOOK 判準八安全掃描：針對上游 PR head（PR #22/#24/#25/#26）與 `b449e7a..a50c73b` 完整 diff
  檢查行內長空白、`eval(`、`new Function(`、超長 base64/hex 或單行超長字串，確認無隱藏內容或惡意注入。

## 驗收證據

Windows 本機已執行：

```text
python -m compileall -q src examples tools tests
python -m py_compile path1_core.py path1_gui.py build_exe.py
python -m ruff check path1_core.py path1_gui.py build_exe.py tests tools
python -m pytest -q
python src/system_health.py
```

Canonical Windows gate：

```powershell
pwsh -NoProfile -File tools\dev_check.ps1
```

結果：全綠通過（`257 passed`，Ruff 全綠，full health 全模組 GREEN，WINDOWS DEV CHECK GREEN）。

## 尚未宣稱的範圍

- 沒有用私人 CapCut 草稿做 destructive/live smoke；草稿修復以合成 8-replica fixture 驗證。
- 沒有安裝 optional OCR 套件；無 OCR 的降級路徑已由 example 06 驗證。
- CapCut Desktop 版本相容性仍以 `TROUBLESHOOTING.md` 的矩陣與使用者本機
  `detect_draft_format()` 結果為準，不能從程式碼 review 推定所有未來版本。
- P4 複核人目前採機器名單（`AI`、`codex` 等）排除，屬君子協定；`file:` 只驗存在、`sha256:` 只驗格式，不驗內容（已知限制，依據 `docs/DECISIONS.md:41`）。
