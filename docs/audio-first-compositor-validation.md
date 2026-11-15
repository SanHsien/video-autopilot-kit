# Audio-First 本機綠幕合成驗收（T-20261115-11）

STATUS: DONE — 以本機合成素材實測通過；聚焦測試 18 passed，完整 Windows gate 綠燈。

日期：2026-11-15。基準 commit：`9d42877`。不安裝套件、不呼叫雲端服務、不登入、不上傳。
實作與測試初稿在無法執行 FFmpeg 的沙盒內寫成；同日在可執行 FFmpeg 的本機修正並量測（見「修正紀錄」）。

## 使用與範圍

```powershell
python src/audio_first_compositor.py voice.wav green.mp4 background.mp4 music.wav result.mp4 --fps 30 --width 1280 --height 720
```

輸入均為本機檔案。配音必須有可讀的 audio-stream duration；視覺素材與 BGM 不足時循環，
全部裁至配音時長向上取整的一格邊界。預設 H.264 / yuv420p、AAC / 48 kHz、固定 30 fps。
尺寸必須為正偶數；不讀其他輸入的音軌。API 與 CLI 可調 key、similarity、blend、despill、
bgm_gain、duck_threshold、duck_ratio；`--help` 列旗標。

```text
配音 stream duration -> ceil(duration * fps) -> 時間軸
綠幕 -> chromakey -> despill -> overlay <- 背景
配音 -> sidechain 控制 BGM -> amix -> limiter -> AAC
                                       |
                            暫存 MP4 -> 排他建立新輸出
```

不覆寫既有輸出（包括輸入本身）；輸入錯誤／編碼失敗不發布輸出。
先在輸出父目錄編碼暫存片，再用 `xb` 排他建立目的檔，避免覆寫競態。
發布階段若寫檔失敗，刪除本次新建的半成品；這不是跨程序的原子可見性保證。

既有 `src/av_util.py` 的 `run` 可重用；其 `duration` 失敗回 0，不適合本次 fail-closed 驗證。
`src/silent_vlog_maker/pipeline.py` 是既有濾鏡組裝，未提供此綠幕與 sidechain 合成契約，故新增獨立模組，未改 GUI／EXE。
一手程式來源：[新模組](../src/audio_first_compositor.py)、[測試](../tests/test_audio_first_compositor.py)、
[共用 subprocess 包裝](../src/av_util.py)、[既有 pipeline](../src/silent_vlog_maker/pipeline.py)。

## 素材與量測方法

測試用 Python 標準庫 `wave` / `array` 生成 48 kHz 單聲道 PCM：配音為 4.013 秒、440 Hz、振幅 0.2，
1–3 秒有聲，其餘靜音；BGM 為 0.5 秒 1000 Hz 固定音（振幅 0.2），由合成器循環。
FFmpeg lavfi 生成 160×128、30 fps、0.5 秒的純綠加紅矩形（48,32 起 64×64）與純藍背景；所有素材均為自行合成。
本切片不含文字、字幕或字型，沒有字型下載或授權相依；沒有使用真人影音或生成服務。

BGM 音量以 1000 Hz 正弦／餘弦投影從解碼後的最終 AAC 中隔離（配音是 440 Hz，不會混入），
比較非旁白區間（0.3–0.8 秒）與旁白區間（1.5–2.5 秒）的振幅。

## 實測結果

環境：Windows 11、`ffmpeg version 9.0.2-full_build-www.gyan.dev`（`ffmpeg -version`／`ffprobe -version` 實跑）、
Python 3.14.10、pytest 9.2.0、Ruff 0.17.3。目標配音時長 4.013 秒，固定 30 fps，一格 = 0.033333 秒。

| DoD | 門檻 | 實測值 | 結果 |
| --- | --- | --- | --- |
| 時長（container） | 與 4.013 秒相差 ≤ 0.033333 秒 | 4.033333 秒，差 0.020333 秒（0.61 格） | 通過 |
| 時長（video stream） | 同上 | 4.033333 秒、121 格 | 通過 |
| 時長（audio stream） | 同上 | 4.033333 秒 | 通過 |
| stream | 一條視訊＋一條音訊 | h264 / yuv420p ＋ aac / 48000 Hz / 單聲道 | 通過 |
| fps／解析度 | 30/1、160×128 | `r_frame_rate` 與 `avg_frame_rate` 皆 30/1、160×128 | 通過 |
| 可解碼 | `ffmpeg -v error -xerror -i out -f null -` exit 0、無輸出 | exit 0、無輸出 | 通過 |
| 前景取樣 (80,64)，t=2 秒 | 與 (255,0,0) 各通道差 ≤ 20 | (252, 0, 0)，最大差 3 | 通過 |
| 背景取樣 (16,16)，t=2 秒 | 與 (0,0,255) 各通道差 ≤ 20 | (0, 0, 254)，最大差 1 | 通過 |
| BGM ducking | 旁白區間比非旁白區間低 ≥ 6 dB | 振幅 0.050024 → 0.001801，降 28.87 dB | 通過 |
| BGM 恢復 | 3.5–3.9 秒與旁白前相差 < 1 dB | 振幅 0.050021，差 −0.0004 dB | 通過 |
| 配音保留 | 440 Hz 振幅 > 0.1 | 0.199966 | 通過 |
| 峰值 | 不削波（< 1.0） | 0.2021 | 通過 |
| 錯誤輸入 | 明確失敗、不產生或覆寫輸出 | 見下表 | 通過 |

合成成品 SHA256（160×128 測試片）：`5af7ab8e8ecc5df5704c2148e9349a7b5b4b49e501d8ef27a77b42fdaa645709`。
編碼結果與 FFmpeg／libx264 版本有關，其他版本的雜湊可能不同。

錯誤輸入案例（全部在 `tests/test_audio_first_compositor.py`，最後一列除外）：

| 案例 | 預期 | 實測 |
| --- | --- | --- |
| 不合法參數 7 種（fps 0、奇數寬、NaN、inf、key 注入字串、ratio 0、despill −1） | `ValueError`，輸出不存在 | 7 passed |
| 輸出檔已存在 | `FileExistsError`，內容仍是 `keep` | passed |
| 輸出路徑指向輸入檔 | `FileExistsError`，四個輸入位元組不變 | passed |
| 配音位置給了沒有音軌的影片 | `ValueError`（audio stream），輸出不存在 | passed |
| 配音檔損毀 | `ValueError`（Cannot probe），輸出不存在 | passed |
| 編碼失敗（模擬 ffmpeg 回非零） | `ValueError`，輸出與暫存目錄都不留 | passed |
| 配音時長未知／0／NaN／inf／負值 5 種 | `ValueError`，輸入不變 | 5 passed |
| 編碼途中別人先寫了輸出檔 | `FileExistsError`，對方內容保留 | passed |
| CLI 給不存在的輸入 | exit 1、stderr 有 `ERROR:`，輸出不存在 | passed |
| CLI 對已存在的輸出重跑（手動） | exit 1、`ERROR: Output already exists; refusing to overwrite` | 符合 |

## 命令與結束碼

```powershell
# 聚焦測試；成品排他寫到 repo 外的目錄
$env:AUDIO_FIRST_ARTIFACT_DIR = '<repo 外的目錄>'
python -m pytest -q -s tests/test_audio_first_compositor.py        # exit 0，18 passed
# 從 repo 上一層的 cwd 再跑一次
python -m pytest -q <repo>/tests/test_audio_first_compositor.py -p no:cacheprovider   # exit 0，18 passed

# 對 repo 外成品獨立量測
ffprobe -v error -show_entries stream=codec_type,codec_name,pix_fmt,width,height,r_frame_rate,avg_frame_rate,nb_frames,duration,sample_rate,channels:format=duration,format_name -of json audio-first-synthetic.mp4
ffmpeg -v error -xerror -i audio-first-synthetic.mp4 -f null -     # exit 0，無輸出

# CLI 以預設 1280×720 實跑同一組素材
python src/audio_first_compositor.py voice.wav green.mp4 blue.mp4 music.wav cli-720p.mp4   # exit 0
ffprobe ... cli-720p.mp4          # h264 1280×720 30/1、121 格、4.033333 秒；aac 4.033333 秒
ffmpeg -v error -xerror -i cli-720p.mp4 -f null -                  # exit 0
python src/audio_first_compositor.py voice.wav green.mp4 blue.mp4 music.wav cli-720p.mp4   # exit 1，拒絕覆寫

# 完整 Windows gate
pwsh -NoProfile -File tools\dev_check.ps1                          # exit 0，pytest 275 passed，HEALTH GREEN
```

測試片素材由測試 fixture 產生，命令為
`ffmpeg -nostdin -v error -f lavfi -i "color=c=0x00ff00:s=160x128:r=30:d=0.5" -vf "drawbox=x=48:y=32:w=64:h=64:color=red:t=fill" -c:v libx264 -pix_fmt yuv420p green.mp4`
（背景把顏色換成 `blue`、不加 `-vf`）。合成影片與素材只放在 repo 外的暫存目錄，量測後已刪除，沒有提交任何媒體。

## 修正紀錄

- 測試 fixture 的 lavfi 參數原寫 `d=.5`；FFmpeg 9.0.2 回 `Unable to parse "d" option value ".5" as duration`，
  四個用到素材的測試全部 error。改成 `d=0.5`。
- `test_cli_missing_input` 原用相對路徑 `src/audio_first_compositor.py`；pytest 的 cwd 不是 repo 根目錄時
  Python 找不到腳本回 exit 2，斷言 `== 1` 失敗。改用由測試檔位置算出的絕對路徑，並補斷言輸出不存在。
- 驗收測試補上 audio stream 時長與 `nb_frames == 121` 斷言；斷言門檻沒有放寬，沒有新增 skip。
- 實作 `src/audio_first_compositor.py` 實測後不需修改。

## 重複性檢查

`src/` 內沒有其他檔案使用 `chromakey`、`colorkey`、`despill`、`sidechaincompress` 或 `amix`（`grep` 查證）。
既有的 `overlay` 濾鏡出現在 `silent_vlog_maker`、`longform_maker/screen_clean.py` 與 `capcut_helpers/delivery_qa.py`，
都是一般疊圖／置中，不做綠幕去背或 BGM 壓低。
本模組重用 `src/av_util.py` 的 `run`；沒有重用 `av_util.duration`，因為它失敗時回 0，不適合 fail-closed。

## 限制

- 量測只支持這組固定合成素材，不代表任意旁白必定衰減 6 dB。壓縮器依輸入振幅、閾值與比例反應；
  真實素材須調參並聽驗。
- 純色塊的取樣點離邊緣很遠，沒有量測去背邊緣、溢色或半透明區域的品質。
- 輸入會直接拉伸至指定尺寸，未處理保比例裁切、HDR、字幕或響度標準（如 LUFS）。
- 配音必須有 audio-stream duration；容器沒寫 stream 時長的格式會被拒絕，不猜測。
- 只在 Windows 11 + FFmpeg 9.0.2 實測；其他平台與版本未查證。
- 發布階段是「暫存編碼 → 排他建立」，不是跨程序的原子可見性保證。
- 缺 ffmpeg／ffprobe 時素材測試會 skip，那種結果不算通過影音驗收。

濾鏡文件（2026-11-15 查閱）：[chromakey](https://ffmpeg.org/ffmpeg-filters.html#chromakey)、
[despill](https://ffmpeg.org/ffmpeg-filters.html#despill)、
[sidechaincompress](https://ffmpeg.org/ffmpeg-filters.html#sidechaincompress)、
[amix](https://ffmpeg.org/ffmpeg-filters.html#amix)、[alimiter](https://ffmpeg.org/ffmpeg-filters.html#alimiter)。
線上文件對應開發版；本模組用到的選項由 9.0.2 實際執行成功間接驗證，未逐項比對文件。
