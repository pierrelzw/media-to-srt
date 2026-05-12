---
name: media-to-srt
description: Transcribe a video or audio file (URL or local) into an SRT subtitle file using whisper.cpp or Douban ASR. Supports any yt-dlp-compatible platform (YouTube, Bilibili, Xiaohongshu/小红书, Douyin/抖音, Vimeo, Twitter/X, etc.) plus local audio files (m4a/mp3/wav/aac/flac). Use this skill whenever the user asks to "transcribe a video", "转录视频", "提取字幕", "generate subtitles", "视频转文字", "get transcript from video", "语音转文字", "转录音频", "转录播客", "播客转文字", "transcribe audio", "transcribe podcast", "voice memo", or provides a video/audio URL or local path (including .m4a/.mp3/.wav) and wants speech-to-text output. Support both local whisper.cpp (default, no credentials) and cloud Douban ASR (faster, supports speaker diarization). This is the right skill even if the user says "转成文本" or just "transcribe" — SRT is the default output because timestamps are almost always useful.
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

### 2. Transcribe using CLI tool

**Auto-detect backend** (Douban Flash if credentials available, else whisper.cpp):
```bash
python3 <media-to-srt>/bin/transcribe.py "$PREFIX.<ext>"
```

**Force specific backend**:
```bash
# Douban Flash (fast, < 5 sec)
python3 <media-to-srt>/bin/transcribe.py "$PREFIX.<ext>" --backend flash

# Douban Standard (large files, async polling)
python3 <media-to-srt>/bin/transcribe.py "$PREFIX.<ext>" --backend standard

# whisper.cpp (local, offline)
python3 <media-to-srt>/bin/transcribe.py "$PREFIX.<ext>" --backend whisper
```

**Advanced options**:
```bash
# Specify output path
python3 <media-to-srt>/bin/transcribe.py "$PREFIX.<ext>" -o subtitles.srt

# Generate both SRT and TXT
python3 <media-to-srt>/bin/transcribe.py "$PREFIX.<ext>" --output-txt transcript.txt

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

## Output format

Default output is SRT with timestamps and optional speaker labels.

### SRT with speaker diarization (Douban ASR)

```
1
00:00:00,000 --> 00:00:05,000
[Speaker_1] Hello, welcome to the podcast.

2
00:00:05,500 --> 00:00:10,000
[Speaker_2] Thanks for having me!
```

### Plain text output

If user asks for plain text (纯文本 / txt / "just the text"):
```bash
python3 <media-to-srt>/bin/transcribe.py "$PREFIX.<ext>" --output-txt output.txt
```

Generates text file with speaker labels stripped.

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
