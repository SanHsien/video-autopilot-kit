# 貢獻指南

## 開始前

1. 先讀 `AGENTS.md`、`FORK.md` 與相關使用文件。
2. 確認問題在最新 `main` 仍可重現，並查過既有 Issues。
3. 不要附上私人影片、音訊、逐字稿、CapCut 草稿或任何憑證。

## 本機開發

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\python -m pytest -q
.venv\Scripts\python src\system_health.py --quick
```

需要完整 ffmpeg 驗證時，再執行：

```powershell
.venv\Scripts\python src\system_health.py
```

## Pull Request

- 一個 PR 聚焦一個問題。
- Bug 修正先附失敗測試；新行為需涵蓋成功、邊界與錯誤路徑。
- 修改使用方式時同步更新 README／SETUP／TROUBLESHOOTING。
- 說明是否來自 upstream、是否保留相容性，以及實際跑過哪些指令。
- 提交訊息建議使用 `fix:`、`feat:`、`docs:`、`test:`、`chore:`。
