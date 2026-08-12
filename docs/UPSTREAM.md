# 上游維護

## Remote

- Fork：`origin` → `https://github.com/SanHsien/video-autopilot-kit.git`
- 原作者：`upstream` → `https://github.com/Hao0321/video-autopilot-kit.git`
- 追蹤分支：`main`

## 檢查新提交

```powershell
git fetch upstream main
python tools\check_upstream_updates.py --strict
```

本 fork 與上游目前都有自己的 `v0.13.0`，且指向不同 commit／產品內容。不要用
`git fetch upstream --tags` 把兩邊 tag 拉進同一 namespace；需要比對上游 tag 時使用
`git ls-remote --tags upstream`，並以 commit SHA 而非同名 tag 作審查水位。

工具會以 `tools/upstream_baseline.json` 的 `reviewed_through` 為起點，列出所有未審查提交。
有新提交或檢查失敗時，`--strict` 回傳非零；排程 workflow 也會因此明確失敗。

## 審查清冊

每次只做一次批次審查：

1. 讀 commit 主旨與變更檔案。
2. 判斷是否與 fork 修正、測試、Windows/CJK 路徑或文件衝突。
3. 可直接同步的提交用 merge/rebase；只需要部分修正時 cherry-pick 或重新實作最小差異。
4. 跑 focused pytest、`system_health.py --quick`；碰到影音模組再跑 full health。
5. 在 `docs/DECISIONS.md` 記錄採用／略過理由。
6. 驗證完成後才把 baseline 推進到已審查的完整 40 字元 SHA。

Baseline 代表「已審查」，不代表「全部已合併」。

## 2026-08-12：上游 v0.13.0 commits、issues、PR review

本輪審查上游 `main` 從 `de4cef7` 到 `0aeaf48` 的三個 commits，並檢查全部 issues／PR：

- 上游沒有 standalone issue；GitHub 顯示的 3 個 open issues 全是 PR #1、#2、#3。
- PR #4、#5、#6 已合併，依序形成下表三個 `main` commits。
- PR #3 仍是 draft，檢查 head `196050992cdff7622afb706fbc36f98bd8be57c1`，沒有 CI checks。
- PR #1、#2 沒有新 commit 或狀態變化，維持 2026-08-09 的 superseded 結論。

| Commit／PR | 結論 | 理由與證據 |
|---|---|---|
| `fb1fc8f` / PR #4 safe updater + storage lifecycle | **不直接合併；拆成後續 fork migration。** | Updater 的 project ID、channel、release notes 與 Skill auto-update 都指向 `Hao0321`；本 fork 已有不同內容的 `v0.13.0` 與 Path 1 GUI/EXE，原樣採用會把 fork 判成 CURRENT，或在後續版本用上游 managed files 取代 fork。Shorts 成片也從 `<spec name>.mp4` 改為 `current.mp4`，是需要 GUI、文件、回溯相容與清理失敗測試的輸出契約變更。 |
| `f4527c4` / PR #5 deterministic archive normalization | **概念採用、程式暫緩。** | UTF-8/LF 正規化後 deterministic ZIP 的作法合理，且上游兩次 build hash 相同；但程式只存在於目前不相容的 updater，等 fork 自己的 source-release contract 定案後再移植。 |
| `0aeaf48` / PR #6 release date | **略過。** | 只修改上游 v0.13.0 CHANGELOG 日期，不能覆蓋本 fork 已在 2026-08-09 發布的同名版本紀錄。 |
| PR #3 `Harden video autopilot production workflow` | **維持 deferred，等離開 draft 且 head 改變後重審。** | 量測分鏡格線、正式 MP4 contact sheet、口白試聽與音訊 QA 原則有價值；但 PR 新增第二套 `skills/video-autopilot/`，與上游剛合併的 `codex-skill/video-autopilot/` 重複，且要求 `output/final_v[N].mp4`，直接違反 PR #4 的 current-only/versioned-output blocked 契約。YT_music／ACE-Step 也不是此 repo 可驗證的內建依賴。 |

### 阻擋直接合併的 findings

| ID | 嚴重度 | Finding | 處理 |
|---|---|---|---|
| U13-01 | High | 上游 updater 的發行身分與 channel 硬編碼為 `Hao0321/video-autopilot-kit`；同名 `v0.13.0` 又讓本 fork 無法用 SemVer 區分兩套內容。 | 不引入 updater／Skill auto-update。若未來採用，必須先建立 fork 專用 project/channel、升版與從現行 `98bccee` 遷移的測試 fixture。 |
| U13-02 | High | 實際上游 release ZIP（SHA-256 `7952d314305c19e8ad60101dbc4268432ea57ff2e4d63bc05b71b0c19005529a`）有 125 entries，但沒有 `.gitignore`；同時 manifest 的 deny pattern 沒命中仍存在的 `D:/creator0321_YT_Claude/assets/bgm`，release self-test 仍回 GREEN。 | 不把該 ZIP／manifest 當 fork 發布來源；fork 保留自己的中性路徑契約與媒體 ignore。未來 source archive 必須把 `.gitignore` 列為 required 並用 regression test 驗證私人路徑。 |
| U13-03 | Medium | `finalize_success()` 先永久刪 transient，再做 registered-path 與 output-policy 驗證；後段失敗時 debug evidence 已消失，不符合 fail-closed cleanup。 | storage lifecycle 暫不接入正式 Shorts；移植時須先完整 validate、再一次執行 cleanup，並覆蓋失敗不刪檔測試。 |
| U13-04 | Medium | 上游 PR #4–#6 沒有 GitHub checks；內建 self-test/full health 全綠，但 release archive 不含 pytest suite，無法證明 fork 的 public Shorts API、Windows GUI 與 EXE contract。 | 只把 upstream self-test 當補充證據；fork 仍以 `tools/dev_check.ps1` 與 Windows/Ubuntu CI 為合併 gate。 |

### 本輪驗證

在 detached upstream worktree 實際執行：

```text
python -m compileall -q src install_or_upgrade.py
python src/storage_lifecycle.py selftest
python src/release_manager.py selftest
python src/system_health.py --quick
python src/system_health.py
python -m bandit -q -ll src/release_manager.py src/storage_lifecycle.py install_or_upgrade.py
```

compile、兩個 self-test、quick/full health 與 Bandit medium/high 均通過；另下載正式 release
assets，確認 channel/archive SHA-256 一致並逐項檢查 ZIP 內容。這些成功證據不消除上表的
fork identity、manifest coverage 與 cleanup ordering 問題。

## 2026-08-09：上游 open PR review

本輪檢查 [`Hao0321/video-autopilot-kit` 的兩個 open PR](https://github.com/Hao0321/video-autopilot-kit/pulls)。
兩者都建立於 2026-06、沒有 CI check，且目前 upstream/fork 已演進到 v0.12。

| PR | 結論 | 現行證據 |
|---|---|---|
| [#1 `fix: import crash in capcut_helpers + scrub residual author PII`](https://github.com/Hao0321/video-autopilot-kit/pull/1) | **不合併；已被後續實作完整取代。** PR 對目前上游標示 conflicting，舊 `DEFAULT_CAPTION_KEYWORD_MAP` rename 也會倒退現行公開 API。 | `import capcut_helpers` 成功；`text_style.py` 在需要 `Path.home()` 的分支內 lazy import；現行 `EXAMPLE_KEYWORD_MAP` 是中性示例並保留 zero-config filename matching；PR 指出的六個私人 identifier 在 `src/capcut_helpers/` 全數不存在。 |
| [#2 `fix: add missing pathlib import in text_style.py`](https://github.com/Hao0321/video-autopilot-kit/pull/2) | **不合併；同一 bug 已被後續 lazy import 修復。** 直接 cherry-pick 只會多一個重複 global import。 | `get_capcut_font_path()` 的 SystemFont 分支在使用前執行 `from pathlib import Path`；package import 與完整 Windows health 均成功。 |

聚焦驗證：

```powershell
.venv\Scripts\python -c "import sys; sys.path.insert(0, 'src'); import capcut_helpers"
rg -n -i "hao0321|game\.hao0321|HAO SURVIVOR|01-42-43|01-44-29|01-44-04" src\capcut_helpers
```

第二個指令預期找不到結果（exit 1）。本輪沒有推進 `tools/upstream_baseline.json`：兩個 PR
都不是 `upstream/main` 的新 commit，baseline 仍正確代表 main 已審查到的 SHA。
