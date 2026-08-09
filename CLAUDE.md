# CLAUDE.md

請先完整閱讀並遵守 [`AGENTS.md`](AGENTS.md)。本檔只補充 Claude Code 的最小入口：

- 這是保留上游歷史的 fork；不要移除 `upstream`、原作者或 MIT 授權標示。
- 修改公開範例或 gate 前，先跑對應 pytest；提交前跑
  `pwsh -NoProfile -File tools\dev_check.ps1` 完整 Windows gate。
- 影片、字幕、profile、CapCut 草稿與本機輸出一律不可提交。
- 外部服務整合先讀 `docs/INTEGRATIONS.md` 的資料保留與人工交接邊界。
- 修改 Path 1 GUI 或封裝時先讀 `docs/PATH1_GUI.md`；GUI 必須重用 `path1_core.py`，不得
  在 Tkinter event handler 複製剪輯規則或同步執行長時間 ffmpeg 工作。
- EXE 完成證據包含重新建置、`--diagnose-file` 四項依賴全綠與 `--smoke-test`，不能只看 pytest。
- 使用繁體中文，直接交付可驗證結果，避免冗長背景鋪陳。
