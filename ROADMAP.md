# 路線圖

> 本 repo 後續工作的單一真相源。做完一項，就在同一個 commit 刪掉那一列；新工作只加在這裡。
> 現況段的數字是 2026-10-29 依 `main` `5dd5267da240` 查的快照，開工前先重查 GitHub。

## 現況

`video-autopilot-kit` 是 `Hao0321/video-autopilot-kit` 的 Windows-first 維護 fork：ffmpeg 影片工具、CapCut 輔助、Shorts／訪談的機械化 QA gate，以及 Path 1 Tkinter GUI／可攜 EXE（`AGENTS.md:5-13`、`FORK.md`）。最近 release 是 v0.13.0（2026-08-09）；`main` 帶有未發行的 gate fail-closed 修正、Pillow 13 下限與上游三項採用（`CHANGELOG.md:1` 起的 Unreleased 段）。
健康：open issue 0、open PR 0、Dependabot 與 code scanning 告警 0，CI、CodeQL、Upstream check 在 `main` 最近一次皆 success，Dependency freshness 2026-10-25 success（2026-10-29 `gh` 查詢）。與上游「No common ancestor」是已知事實，不是缺陷；上游審查水位在 commit `a50c73b`、PR 29、issue 30（`tools/upstream_baseline.json`）。
卡住的地方：沒有。未發行的變更還沒包成新的 EXE／release（維護者決定）；`REPO_REVIEW.md` 已改寫為現況版本（2026-10-26 深度掃描與現行基準）。

## 近期：可以直接動手

| 項目 | 為什麼 | 驗收方式 | 建議執行者 | 證據 |
| --- | --- | --- | --- | --- |

## 中期：等條件成立再做

| 項目 | 觸發條件 | 驗收方式 | 建議執行者 | 證據 |
| --- | --- | --- | --- | --- |
| 發新版（含 Pillow 13 下限、gate fail-closed 修正、`TONEMAP_FILTER` 與 P4／I-B 行為變更）並重建 Path 1 EXE | 維護者決定發版。發版說明須寫明：既有企劃檔與 `_guest.py` 舊自由格式會失敗必須改寫；Path 1 需 Python 3.12+ | 三處版本字面值同步；CI 的 Windows EXE build 與 `--smoke-test` success；`CHANGELOG.md` 把 Unreleased 改為版本段；GitHub Release 資產可下載並跑得起來 | 維護者 | `CHANGELOG.md` Unreleased 段粗體警語；`docs/DECISIONS.md:16-29`；`docs/PATH1_GUI.md` |
| 處理上游新增項目 | `Upstream check` workflow（週一）轉 failure，代表上游有水位之後的新 commit、PR 或 issue | `docs/DECISIONS.md` 與 `docs/UPSTREAM.md` 各新增一筆判定與理由；水位推進；`python tools/check_upstream_updates.py` 無待審；採用者先有紅燈測試。對照 `docs/DECISIONS.md` 2026-10-25 條目的「觸發條件」（改用 Editkin 渲染、上游再調整 gate 輸入驗證等）決定是否重評已不採用項目 | Claude Sonnet | `.github/workflows/upstream-check.yml:11`；`docs/DECISIONS.md:47-69`；`docs/UPSTREAM.md:36-49` |
| 為 `interview_autopilot` 的 `ep` 加 `[A-Za-z0-9_-]+` 驗證 | 這個工具被包成服務，或讓第三方餵 `ep`（目前只有本機 CLI 使用者自己能傳，不跨信任邊界） | 含 `../` 的 `ep` 被拒絕並有重現測試；`python -m pytest` 綠 | Claude Sonnet | `docs/DECISIONS.md:7-8` |
| `shorts_autopilot.scan` 改成寫暫存檔再改名，避免沿用中斷留下的半成品 `_work/*.mp4` | 出現實際案例（中斷後輸出壞檔被當成已完成） | 先有重現測試：預先放一個截斷的 `_work/*.mp4`，scan 不沿用；`python -m pytest` 綠；行為變更寫進 `CHANGELOG.md` | Claude Sonnet | `docs/DECISIONS.md:9-10` |
| 複核人驗證強化（機器名單前綴比對、`file:`／`sha256:` 內容驗證） | 上游加強同一機制，或實際出現假複核通過 | 假複核人樣本被 gate 擋下的測試；既有合法範本仍通過 | Claude Opus | `docs/DECISIONS.md:41`（已知限制）；`docs/DECISIONS.md` 2026-10-25 條目 |

## 刻意不做

| 不做什麼 | 理由 | 什麼情況下重新考慮 |
| --- | --- | --- |
| 把上游 v0.14 之後的 `publish_hub`、`visual_master`、Editkin 渲染、`*_validation.py` 模組拆分整批合併進來 | 本 fork 沒有對應層，上游批次還把私人識別字串帶回；與 Path 1（ffmpeg＋可攜 EXE）方向相反。逐批判定在 `docs/DECISIONS.md` | 本 fork 決定改以 Editkin 渲染，或上游清掉私人識別字串（`docs/DECISIONS.md` 2026-08-23 條目的觸發條件） |
| 對上游做 `git merge`、補共同祖先或改寫歷史 | 兩邊無共同祖先是已知事實；同步一律逐筆審查後 cherry-pick 或自行最小實作（`AGENTS.md:21`） | 無；不要提議 |
| 啟用 Dependabot 自動合併 | 2026-08-09 已決定不啟用（`docs/DECISIONS.md` 該日條目） | 本 repo 出現持續、低風險、可由分類器判定的依賴 PR 量 |
| 提交影片、音訊、CapCut 草稿、逐字稿、個人 profile 或憑證；代管剪輯服務 | 產品邊界（`AGENTS.md:15-20`） | 不重新考慮 |

## 維護方式

fork：直接推 `main`（`FORK.md`）。上游每週一由 `Upstream check` 檢查，紅燈是上游有未審項目、不是工具壞；依賴新鮮度每月 1 日檢查；發版只在維護者決定時進行，純文件與內部整理不 bump 版本。
