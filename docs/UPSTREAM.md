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
