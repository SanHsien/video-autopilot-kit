# 安全政策

## 支援範圍

安全修正以本 fork 的最新 `main` 為主；上游版本的問題也會視需要回報原作者。

## 私下回報

請使用 GitHub Security Advisories 的 **Report a vulnerability** 私下回報。若該入口不可用，
請透過 GitHub 個人檔案聯絡維護者，不要先建立公開 Issue。

回報請包含影響範圍、重現步驟、受影響版本與最小必要證據。請勿附上真實 API key、cookie、
帳號、私人影音、逐字稿或可識別個人的 CapCut 草稿。

## 特別注意

- 影片與字幕可能含個資、地點、聲紋或未公開內容。
- `config.py`、`profiles/`、媒體、草稿與產出已列入 `.gitignore`，不得用強制加入繞過。
- 第三方轉錄、OCR、CapCut 與平台 API 的資料處理政策不由本 repo 控制；採用前需另行審查。

Path 1 GUI 只把非秘密欄位存到 `%LOCALAPPDATA%\video-autopilot-kit\path1-gui.json`，不會上傳
素材或自動把路徑寫入 repo。螢幕錄影清理只能機械移除頭尾與指定裁切區；中央通知、聊天視窗、
專案名等仍須用交付 QA 的全幀圖人工檢查，不能把「已跑清理」當作沒有隱私洩漏的證據。

可攜 EXE 會執行內嵌 ffmpeg／ffprobe。只使用本 repo 的 `build_exe.py` 從已知本機 binary
distribution 建置，並保留 `path1-build-info.json` 與第三方授權文件；不要用來源不明的同名
執行檔替換 `PATH` 後重新封裝。
