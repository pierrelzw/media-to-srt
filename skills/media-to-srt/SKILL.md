---
name: media-to-srt
description: Transcribe a video or audio file (URL or local) into multiple formats (SRT/JSON/WebVTT/TXT) using whisper.cpp or Douban ASR. Supports any yt-dlp-compatible platform (YouTube, Bilibili, Xiaohongshu/小红书, Douyin/抖音, Vimeo, Twitter/X, etc.) plus local audio files (m4a/mp3/wav/aac/flac). Use this skill whenever the user asks to "transcribe a video", "转录视频", "提取字幕", "generate subtitles", "视频转文字", "get transcript from video", "语音转文字", "转录音频", "转录播客", "播客转文字", "transcribe audio", "transcribe podcast", "voice memo", "词级转录", "word-level transcript", "词时间戳", "karaoke", "卡拉OK", "逐词", or provides a video/audio URL or local path (including .m4a/.mp3/.wav) and wants speech-to-text output. Support both local whisper.cpp (default, no credentials) and cloud Douban ASR (faster, supports speaker diarization). This is the right skill even if the user says "转成文本" or just "transcribe" — SRT is the default output because timestamps are almost always useful. Supports JSON for word-level data and WebVTT for karaoke-style word-by-word timestamps.
---

# media-to-srt

Transcribe speech from a video or audio file into an SRT subtitle file. Accepts a URL (any platform yt-dlp supports), a local video file, or a local audio file (m4a, mp3, wav, aac, flac, etc.).

## Transcription Backends

Three transcription engines available. **Ask the user which they prefer**, or suggest based on file size/language:
- **File < 1min** or want **privacy** → whisper.cpp
- **Fast turnaround** (< 5 sec) → Douban ASR Flash
- **Large file or reliability** → Douban ASR Standard

| | **whisper.cpp** | **Douban Flash** | **Douban Standard** |
|---|---|---|---|
| **Speed** | Slower (local CPU) | ⚡⚡ Fastest (< 5s) | ⚡ Fast (polling) |
| **Max file size** | Unlimited | 100 MB | Unlimited |
| **Privacy** | 🔒 Fully local | Cloud (Bytedance) | Cloud (Bytedance) |
| **Setup** | Free (3GB model) | Free API | Free API |
| **Speaker info** | No | ✓ Yes | ✓ Yes |
| **Languages** | 30+ (auto-detect) | EN, ZH, JA, KO | EN, ZH, JA, KO |
| **API style** | N/A | Single call | Async submit + poll |
| **Best for** | Privacy, any language | Quick transcription | Large files, stability |

## Prerequisites: Common

Check these tools. `yt-dlp` is only needed when the input is a URL; local audio/video files skip it.

```bash
command -v yt-dlp        # brew install yt-dlp  (only needed for URLs)
command -v ffmpeg        # brew install ffmpeg
```

### Option 1: whisper.cpp (default, no credentials needed)

```bash
command -v whisper-cli   # brew install whisper-cpp
ls ~/.local/share/whisper-models/ggml-large-v3-turbo.bin  # whisper model
```

If the whisper model is missing:

```bash
mkdir -p ~/.local/share/whisper-models
curl -L -o ~/.local/share/whisper-models/ggml-large-v3-turbo.bin \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo.bin
```

### Option 2: Douban ASR (cloud-based, faster)

Get API credentials from Douban (Volcengine):
1. Visit [https://console.volcengine.com/speech/service/8](https://console.volcengine.com/speech/service/8)
2. Create a project and API credentials
3. Export to environment:
   ```bash
   export DOUBAO_APP_ID="your-app-id"
   export DOUBAO_ACCESS_TOKEN="your-access-token"
   # Optional: export DOUBAO_RESOURCE_ID="volc.bigasr.auc_turbo"  (default)
   ```

Or store in `~/.doubao-config.env` (loaded automatically):
```bash
DOUBAO_APP_ID=your-app-id
DOUBAO_ACCESS_TOKEN=your-access-token
```

Verify credentials work:
```bash
python3 -c "
import os, httpx, base64, json
from pathlib import Path

app_id = os.getenv('DOUBAO_APP_ID')
token = os.getenv('DOUBAO_ACCESS_TOKEN')
if not app_id or not token:
    print('❌ Doubao credentials not found')
else:
    print('✅ Doubao credentials present')
"
```

## Workflow

Work in the current project directory by default, or `~/Downloads/` if the user doesn't have a clear project context.

### 1. Obtain the media

- **URL** (YouTube, Bilibili, 小红书, 抖音, etc.):
  ```bash
  yt-dlp -o "$PREFIX.%(ext)s" "<URL>"
  ```
- **Local video/audio file**: use as-is, set `$PREFIX` from filename

### 2. Select backend and output format

**Ask the user for both backend and output format** together:

| User says | Backend | Format |
|---|---|---|
| "快速"/"快" (quick) | flash | srt |
| "离线"/"本地" (offline/local) | whisper | srt |
| "大文件" (large file) | standard | srt |
| "词级"/"词时间戳"/"word-level" | standard (or flash for speed) | json |
| "卡拉OK"/"逐词"/"karaoke" | standard (or flash for speed) | webvtt |
| "所有格式"/"all formats" | standard (or flash for speed) | all |

**Auto-detect backend** (Douban Standard if credentials available, else whisper.cpp):
```bash
python3 <media-to-srt>/bin/transcribe.py "$PREFIX.<ext>"
```

**Force specific backend + format**:
```bash
# Douban Flash with JSON word-level data
python3 <media-to-srt>/bin/transcribe.py "$PREFIX.<ext>" --backend flash --format json

# Douban Standard with WebVTT karaoke timestamps
python3 <media-to-srt>/bin/transcribe.py "$PREFIX.<ext>" --backend standard --format webvtt

# whisper.cpp (local, offline) — SRT only
python3 <media-to-srt>/bin/transcribe.py "$PREFIX.<ext>" --backend whisper

# Generate all formats at once
python3 <media-to-srt>/bin/transcribe.py "$PREFIX.<ext>" --format all

# Specify output prefix
python3 <media-to-srt>/bin/transcribe.py "$PREFIX.<ext>" -o my_output --format json
```

**Advanced options**:
```bash
# Show speaker timeline (Douban only)
python3 <media-to-srt>/bin/transcribe.py "$PREFIX.<ext>" --summary

# Specify language (whisper only)
python3 <media-to-srt>/bin/transcribe.py "$PREFIX.<ext>" --backend whisper -l zh
```

**CLI tool behavior**:
1. Auto-selects backend or uses specified one
2. Prints status: `"Selected backend: flash"` or `"Selected backend: whisper"`
3. Transcribes audio with progress
4. Saves `$PREFIX.<ext>.srt` (or specified output path)
5. Prints summary: duration, subtitle count, wall-clock time, speaker info

Output: `$PREFIX.srt` with timestamps and optional speaker labels

### 3. Clean up and deliver

- Remove downloaded video (if URL) and intermediate files
- Display first 10 subtitle entries from SRT file
- Report: 
  - **Backend used**: Flash / Standard / whisper.cpp
  - **Duration**: audio length
  - **Subtitle entries**: total count
  - **Output file**: path to .srt
  - **Speakers detected**: (if Douban ASR with multiple speakers)
  - **Processing time**: wall-clock seconds

## Output formats

### SRT (default) — Subtitle format with timestamps

```
1
00:00:00,000 --> 00:00:05,000
[Speaker_1] Hello, welcome to the podcast.

2
00:00:05,500 --> 00:00:10,000
[Speaker_2] Thanks for having me!
```

Generated with `--format srt` or default (no --format flag).

### TXT — Plain text transcript

```
[Speaker_1] Hello, welcome to the podcast.
[Speaker_2] Thanks for having me!
```

Generated with `--format txt`.

### JSON — Word-level timestamps and full metadata

```json
{
  "metadata": {
    "duration_ms": 10000,
    "speakers": ["Speaker_1", "Speaker_2"],
    "segment_count": 2,
    "word_count": 42
  },
  "segments": [
    {
      "id": 1,
      "start_ms": 0,
      "end_ms": 5000,
      "speaker": "Speaker_1",
      "text": "Hello, welcome to the podcast.",
      "words": [
        {"text": "Hello,", "start_ms": 0, "end_ms": 600, "confidence": 0.95},
        {"text": "welcome", "start_ms": 700, "end_ms": 1200, "confidence": 0.92},
        ...
      ]
    }
  ]
}
```

Generated with `--format json`. Best for downstream NLP processing or word-level analysis.

### WebVTT — Karaoke-style word-by-word timestamps

```vtt
WEBVTT

1
00:00:00.000 --> 00:00:05.000
<v Speaker_1><00:00:00.000><c>Hello,</c><00:00:00.700><c>welcome</c>...

2
00:00:05.500 --> 00:00:10.000
<v Speaker_2><00:00:05.500><c>Thanks</c><00:00:06.200><c>for</c>...
```

Generated with `--format webvtt`. Perfect for karaoke, highlighting, or precise word-level synchronization.

### ALL — Generate all four formats at once

```bash
python3 <media-to-srt>/bin/transcribe.py "$PREFIX.<ext>" --format all
```

Creates: `$PREFIX.srt`, `$PREFIX.txt`, `$PREFIX.json`, `$PREFIX.vtt`

**Note**: JSON/WebVTT/TXT formats require word-level data, only available from **Douban ASR** (flash or standard). whisper.cpp backend supports **SRT only**.

```bash
# ✅ Supported (Douban + JSON)
python3 <media-to-srt>/bin/transcribe.py input.mp3 --backend flash --format json

# ❌ Not supported (whisper + JSON)
python3 <media-to-srt>/bin/transcribe.py input.mp3 --backend whisper --format json
# Error: whisper.cpp backend only supports SRT output
```

## Notes

- **Credentials**: Douban ASR requires free API credentials. whisper.cpp requires no setup beyond model download.
- **Auto-detect**: CLI tool automatically picks Douban Flash if credentials exist, else whisper.cpp
- **Age-restricted content**: Ask user to provide cookies via `--cookies-from-browser chrome`. Don't bypass auth.
- **Platform issues**: Some platforms (Douyin, Xiaohongshu) may need cookies/headers. If yt-dlp fails, suggest user open in browser first.
- **Accuracy**: Both methods are high-quality. Douban ASR is faster; whisper.cpp is fully private.
- **Short clips**: For clips < 5 seconds, accuracy may be lower.
- **Security**: Don't use `--no-check-certificates` or other insecure flags.

## Architecture

The skill uses a Python library in `lib/` with persistent, reusable code:

- `lib/config.py` — Credential management (env vars, ~/.doubao-config.env)
- `lib/doubao_asr.py` — Douban ASR clients (Flash & Standard APIs)
- `lib/srt_converter.py` — Utterances → SRT/TXT conversion, speaker timeline
- `bin/transcribe.py` — CLI tool with auto-detection, error handling, reporting

No code is generated each time — reusable, tested, version-controlled.
