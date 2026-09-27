# Path 1 圖形介面與 Windows EXE

`path1_gui.py` 是 SanHsien fork 的 Windows-first 桌面工作台。它是既有 Programmatic pipeline
的薄層介面，不另做一套剪輯引擎，也不需要 CapCut、登入或外部雲端服務。

## 使用者流程

### Shorts Autopilot

1. 選擇一個專案資料夾，直接放入 `.mp4`／`.mov` 原始素材。
2. 按「掃描素材」：程式會正規化 9:16、產生接觸表、招牌放大圖與 `_plan.py`。
3. 按「開啟 `_plan.py`」，依畫面證據填完 `place`、`what`、`addr`、字幕與 BGM 類別；
   `TODO` 不可殘留。
4. 選擇 BGM 素材庫。其下一層資料夾名稱要與 `_plan.py` 的 `bgm_folder` 相同；找不到時
   會退到 `_通用`，兩者都沒有音檔則停止建置。
5. 按「建置 + QA」：依序執行 Shorts gate、ffmpeg 成片、LUFS／格式／loop QA，並輸出
   `_out/`、`_out/_qa/` 與 `REPORT.md`。
6. 人工逐張確認 `CAPTION_match.jpg` 與 `FIRSTFRAME.jpg`。機器產圖不等於人眼項目已通過。

### 影片工具

- **競品節奏量測**：選一支 MP4 或資料夾，輸出刀速、刀距、LUFS 與節奏主體。OCR 未內嵌，
  因此基礎 EXE 會安全跳過字幕 OCR，不影響其餘量測。
- **交付 QA**：對成片執行頻閃、死黑邊、接觸表與全幀掃描；勾選音訊時再檢查 LUFS、
  尾端靜音與 A-V 同步。結果為 BLOCKED 時不可把它解讀為完成。
- **螢幕錄影清理**：實體裁掉頭尾（各至少 1 秒）、依 `W:H:X:Y` 移除瀏覽器 chrome／工作列，
  使用模糊背景補滿畫布並去除音軌。中央浮窗仍須用交付 QA 全幀圖人工檢查。

## 從原始碼啟動

Windows PowerShell：

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\python -m pip install -r requirements-path1.txt
.venv\Scripts\python path1_gui.py
```

來源模式仍需要系統 `ffmpeg`／`ffprobe` 在 `PATH`。GUI 右上角與「環境與說明」頁會顯示
實際解析到的版本和路徑。

## 建置可攜 EXE

PyInstaller 不跨平台編譯，Windows EXE 必須在 Windows 上建：

```powershell
.venv\Scripts\python -m pip install -r requirements-build.txt
.venv\Scripts\python build_exe.py
```

建置前置條件：

- `ffmpeg.exe`、`ffprobe.exe` 都在 `PATH`。
- 兩者來自同一個 binary distribution，且 distribution 根目錄含 `LICENSE`、`README.txt`。
- FFmpeg configuration 不含 `--enable-nonfree`；若含，建置會直接拒絕。

產物：

- `dist/video-autopilot-path1.exe`：單檔 GUI，內嵌 Python、NumPy、Pillow、ffmpeg、ffprobe。
- `dist/path1-build-info.json`：EXE／ffmpeg／ffprobe SHA-256 與 FFmpeg license 判定。
- `dist/FFmpeg-GPLv3.txt`、`dist/FFmpeg-BUILD-README.txt`：原 binary distribution 文件。
- `dist/THIRD_PARTY_NOTICES.md`：第三方元件與再散布注意事項。

OCR 套件體積大且不是主要流程必要條件，因此不在基礎 EXE；競品量測會沿用原本的 graceful
degradation。若日後要另發 OCR 版，必須獨立標示體積、模型與授權，不可悄悄膨脹基礎版。

## 封裝後驗證

不開視窗驗證內嵌依賴：

```powershell
$exe = (Resolve-Path "dist\video-autopilot-path1.exe").Path
$diag = Join-Path $env:TEMP "path1-diagnostics.json"
$p = Start-Process $exe -ArgumentList @("--diagnose-file", $diag) -Wait -PassThru
if ($p.ExitCode -ne 0) { throw "dependency diagnostics failed" }
Get-Content $diag
```

建立完整 Tk UI 後自動關閉：

```powershell
$p = Start-Process $exe -ArgumentList "--smoke-test" -Wait -PassThru
if ($p.ExitCode -ne 0) { throw "GUI smoke failed" }
```

正式驗收至少要同時證明：

1. EXE 有合法 PE `MZ` header 且非空。
2. diagnostics 中四個核心依賴都是 `ok=true`；ffmpeg／ffprobe 路徑位於 PyInstaller
   `_MEI…/bin`，不是系統安裝。
3. GUI smoke 退出碼 0，結束後沒有殘留 `video-autopilot-path1` process。
4. 用合成素材完成至少一個 Path 1 adapter smoke；不在 CI 下載或提交真實素材。

## 設定與資料邊界

GUI 只把欄位值存到 `%LOCALAPPDATA%\video-autopilot-kit\path1-gui.json`，不寫進 repo。
設定內不存帳密、token 或媒體內容。素材、`_plan.py`、輸出影片、QA 圖與日誌都由使用者選擇
本機位置，仍受 [`AGENTS.md`](../AGENTS.md) 的「不得提交私人／媒體資料」邊界約束。

第三方授權與再散布條件見 [`THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md)。
