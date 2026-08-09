# Fork 維護說明

本 repo fork 自 [`Hao0321/video-autopilot-kit`](https://github.com/Hao0321/video-autopilot-kit)，
沿用 MIT License 與完整 Git 歷史。

## 為什麼維護 fork

- 保留原作者持續更新的知識庫與影片工具。
- 採 Windows-first 維護：Windows 11 + PowerShell 是主要開發、除錯與完整驗收環境。
- 建立可重現的 Windows 開發環境、pytest、Windows/Ubuntu CI、CodeQL 與上游追蹤。
- 修復會阻塞本地採用、但尚未進入上游的回歸。
- 提供 Path 1 Windows GUI、可攜 EXE 與內嵌依賴的可驗證建置流程。
- 將本機 profile、媒體與第三方服務資料隔離在 Git 之外。

## 分支與 remote

- `origin/main`：SanHsien 維護線。
- `upstream/main`：Hao0321 原始專案。
- 功能與修正使用短期分支；驗證通過後再合併到 `main`。

同步方式與審查清冊見 [`docs/UPSTREAM.md`](docs/UPSTREAM.md)。fork 專屬決策見
[`docs/DECISIONS.md`](docs/DECISIONS.md)。最近一次完整 repo review 見
[`REPO_REVIEW.md`](REPO_REVIEW.md)；提交前執行 `pwsh -NoProfile -File tools\dev_check.ps1`。
Path 1 GUI／EXE 的使用與封裝邊界見 [`docs/PATH1_GUI.md`](docs/PATH1_GUI.md)。
