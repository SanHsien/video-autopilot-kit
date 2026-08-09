# Repository review（Windows-first）

- Review date: 2026-08-09
- Review baseline: fork `3176b36169214a9987dc6c22fda54ede07e2429c`
- Upstream reviewed through: `de4cef7b347127eeb378985755cd90586758adf5`
- Primary environment: Windows 11、PowerShell、Python 3.14、ffmpeg 9
- Status: 已修復本輪確認的 bug；最新驗收證據以本文件為準

## 結論

這個 fork 值得繼續使用，且適合作為 Windows-first 的本機 AI 剪輯工具箱。公開的六個範例、
核心 gate 與真 ffmpeg health 都能在 Windows 執行；本輪主要風險不是剪輯演算法，而是
CapCut 草稿一致性、Windows 程序驗證、CP950/UTF-8 邊界與自動流程的 fail-closed 行為。

本輪沒有保留未修的 high/medium finding。Bandit medium/high 掃描為 0，`requirements-dev.txt`
的 pip-audit 沒有已知漏洞。

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

## 已檢查但不列為 finding

- 所有外部程序使用 argv list，沒有 `shell=True`、`os.system()`、`eval()` 或 `exec()` 注入面。
- Bandit 的 low-level B603/B607 是本機 `ffmpeg`、`ffprobe`、PowerShell 可執行檔探測；PATH 由
  操作者控制，參數沒有拼成 shell command，因此本輪不改成硬編碼絕對路徑。
- `silent_vlog_maker.audit.audit_raw_files()` 的區域 closure 在每個 clip 迴圈內同步建立並立即消費，
  Ruff B023 不會跨 iteration 延後執行，屬誤報。
- `silent_vlog_maker.helpers` 是相容用 re-export facade；其 F401 是公開 API，不可自動刪除。
- `src/` 內大量 assert 位於 `__main__` self-test；它們不是 production guard，保留可讀性。

## 驗收證據

Windows 本機已執行：

```text
python -m compileall -q src examples tools tests
python -m pytest -q
python src/system_health.py --quick
python src/system_health.py
python examples/01_vertical_short.py
python examples/02_caption_broll_match.py
python examples/03_premium_fx.py
python examples/04_shorts_gate.py
python examples/05_interview_plan.py
python examples/06_teardown.py
python -m bandit -q -ll -r src tools -x tests
python -m pip_audit -r requirements-dev.txt --progress-spinner off
```

Canonical Windows gate：

```powershell
pwsh -NoProfile -File tools\dev_check.ps1
```

本輪結果：`41 passed`、Ruff 全綠、full health 全模組 GREEN、pre-commit 全 hooks 通過。

## 尚未宣稱的範圍

- 沒有用私人 CapCut 草稿做 destructive/live smoke；草稿修復以合成 8-replica fixture 驗證。
- 沒有安裝 optional OCR 套件；無 OCR 的降級路徑已由 example 06 驗證。
- CapCut Desktop 版本相容性仍以 `TROUBLESHOOTING.md` 的矩陣與使用者本機
  `detect_draft_format()` 結果為準，不能從程式碼 review 推定所有未來版本。

## 上游 open PR 評估

2026-08-09 另審查上游 PR [#1](https://github.com/Hao0321/video-autopilot-kit/pull/1) 與
[#2](https://github.com/Hao0321/video-autopilot-kit/pull/2)。兩者處理的 import crash 與私人
keyword map 已被現行 v0.12 實作完整取代，因此不重複合併；逐項證據與 skip 理由見
[`docs/UPSTREAM.md`](docs/UPSTREAM.md)。
