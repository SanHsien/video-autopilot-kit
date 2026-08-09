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
