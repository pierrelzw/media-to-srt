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

Or store in `~/.doubao-credentials.env` (sourced automatically if present):
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

Work in the current project directory by default, or `~/Downloads/` if the user doesn't have a clear project context. Use a sanitized version of the video/audio title or filename as `$PREFIX`.

### 1. Obtain the media

- **URL** (YouTube, Bilibili, 小红书, 抖音, etc.):
  ```bash
  yt-dlp -o "$PREFIX.%(ext)s" "<URL>"
  ```
- **Local video file**: use as-is, set `$PREFIX` from the filename (without extension).
- **Local audio file** (e.g., `.mp3`, `.m4a`, `.wav`, `.aac`, `.flac`): skip yt-dlp entirely. Set `$PREFIX` from the audio filename without its extension.

### 2. Choose transcription backend

**Detect audio duration** (for large file handling):
```bash
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1:noprint_wrappers=1 "$PREFIX.<ext>" | cut -d. -f1
# Output: seconds as integer
```

**Select backend** based on user intent or auto-detect:

| User says | Backend | Reason |
|---|---|---|
| "fast" / "快速" / "quick" | Douban Flash | Fastest (~1s per min audio) |
| "standard" / "大文件" / "reliable" | Douban Standard | Handles any file size |
| "offline" / "离线" / "private" / "local" | whisper.cpp | No cloud/credentials needed |
| **Auto-detect** (no hint) | See below | Based on credentials + file size |

**Auto-detect when user doesn't specify**:
```
If DOUBAO_APP_ID env var is NOT set:
  → use whisper.cpp (no credentials)

If DOUBAO_APP_ID is set:
  If file_size_mb < 100 AND duration_sec < 600 (10 min):
    → use Douban Flash (fastest, good for typical clips)
  Else:
    → use Douban Standard (handles large files, stable)
```

Print to user: `"🚀 Using <Backend> for fast transcription"` or `"🔒 Using whisper.cpp (offline, no credentials)"` so they know which path is active.

### 3A. Douban ASR Path (faster, supports speaker info)

**Setup**: Verify credentials are set:
```bash
source ~/.doubao-credentials.env 2>/dev/null || true
[ -z "$DOUBAO_APP_ID" ] && echo "❌ Missing DOUBAO_APP_ID" && exit 1
```

**Transcribe** (supports multiple audio formats directly):
```python3
import os, base64, json, time, httpx
from pathlib import Path

wav_path = Path("$PREFIX.<ext>")  # Can be mp3, m4a, wav, ogg, flac, webm, mp4
raw = wav_path.read_bytes()
b64 = base64.b64encode(raw).decode()

headers = {
    "X-Api-App-Key": os.getenv("DOUBAO_APP_ID"),
    "X-Api-Access-Key": os.getenv("DOUBAO_ACCESS_TOKEN"),
    "X-Api-Resource-Id": os.getenv("DOUBAO_RESOURCE_ID", "volc.bigasr.auc_turbo"),
    "X-Api-Request-Id": "request-" + str(int(time.time())),
    "X-Api-Sequence": "-1",
    "Content-Type": "application/json",
}

body = {
    "user": {"uid": os.getenv("DOUBAO_APP_ID")},
    "audio": {"format": wav_path.suffix[1:].lower(), "data": b64},
    "request": {
        "model_name": "bigmodel",
        "enable_itn": True,
        "enable_punc": True,
        "show_utterances": True,
        "enable_speaker_info": True,
    },
}

resp = httpx.post(
    "https://openspeech.bytedance.com/api/v3/auc/bigmodel/recognize/flash",
    headers=headers,
    json=body,
    timeout=120.0
)

if resp.status_code != 200:
    raise Exception(f"ASR failed: {resp.status_code} {resp.text}")

result = resp.json()["result"]
utterances = result.get("utterances", [])
```

**Convert utterances to SRT**:
```python3
def utterances_to_srt(utterances, output_path):
    """Convert Douban ASR utterances to SRT format."""
    with open(output_path, "w", encoding="utf-8") as f:
        for i, utt in enumerate(utterances, 1):
            start_ms = utt.get("start_time", 0)
            end_ms = utt.get("end_time", 0)
            text = utt.get("text", "")
            speaker = utt.get("additions", {}).get("speaker") or ""
            
            start = f"{start_ms//3600000:02d}:{(start_ms%3600000)//60000:02d}:{(start_ms%60000)//1000:02d},{start_ms%1000:03d}"
            end = f"{end_ms//3600000:02d}:{(end_ms%3600000)//60000:02d}:{(end_ms%60000)//1000:02d},{end_ms%1000:03d}"
            
            if speaker:
                text = f"[{speaker}] {text}"
            
            f.write(f"{i}\n{start} --> {end}\n{text}\n\n")

utterances_to_srt(utterances, "$PREFIX.srt")
```

Output: `$PREFIX.srt` with speaker labels if available.

### 3B. Douban Standard Path (reliable, large files)

**Setup**: Verify credentials are set:
```bash
source ~/.doubao-credentials.env 2>/dev/null || true
[ -z "$DOUBAO_APP_ID" ] && echo "❌ Missing DOUBAO_APP_ID" && exit 1
```

**Submit audio file**:
```python3
import os, base64, json, time, httpx
from pathlib import Path

wav_path = Path("$PREFIX.<ext>")
raw = wav_path.read_bytes()
b64 = base64.b64encode(raw).decode()

headers = {
    "X-Api-App-Key": os.getenv("DOUBAO_APP_ID"),
    "X-Api-Access-Key": os.getenv("DOUBAO_ACCESS_TOKEN"),
    "X-Api-Resource-Id": os.getenv("DOUBAO_RESOURCE_ID", "volc.bigasr.auc"),
    "X-Api-Request-Id": "request-" + str(int(time.time())),
    "X-Api-Sequence": "-1",
    "Content-Type": "application/json",
}

body = {
    "user": {"uid": os.getenv("DOUBAO_APP_ID")},
    "audio": {"format": wav_path.suffix[1:].lower(), "data": b64},
    "request": {
        "model_name": "bigmodel",
        "enable_itn": True,
        "enable_punc": True,
        "show_utterances": True,
        "enable_speaker_info": True,
    },
}

resp = httpx.post(
    "https://openspeech.bytedance.com/api/v3/auc/bigmodel/submit",
    headers=headers,
    json=body,
    timeout=30.0
)

if resp.status_code != 200:
    raise Exception(f"Submit failed: {resp.status_code}")

submit_result = resp.json()
task_id = submit_result["result"]["task_id"]
```

**Poll for completion** (status codes: `20000000` = done, `20000001/20000002` = processing):
```python3
max_polls = 600  # ~10 min with 1s interval
poll_interval = 1.0

for attempt in range(max_polls):
    time.sleep(poll_interval)
    
    query_body = {"user": {"uid": os.getenv("DOUBAO_APP_ID")}, "task_id": task_id}
    query_resp = httpx.post(
        "https://openspeech.bytedance.com/api/v3/auc/bigmodel/query",
        headers=headers,
        json=query_body,
        timeout=30.0
    )
    
    if query_resp.status_code != 200:
        raise Exception(f"Query failed: {query_resp.status_code}")
    
    query_result = query_resp.json()
    status = query_result.get("status_code", "")
    
    if status == "20000000":  # SUCCESS
        result = query_result.get("result", {})
        utterances = result.get("utterances", [])
        break
    elif status in ("20000001", "20000002"):  # PROCESSING
        print(f"⏳ Processing... ({attempt+1}/{max_polls})")
        continue
    else:
        raise Exception(f"Unexpected status: {status} — {query_result}")
else:
    raise Exception("Timeout: transcription took > 10 minutes")
```

**Convert utterances to SRT** (same as Douban Flash):
```python3
def utterances_to_srt(utterances, output_path):
    """Convert Douban ASR utterances to SRT format."""
    with open(output_path, "w", encoding="utf-8") as f:
        for i, utt in enumerate(utterances, 1):
            start_ms = utt.get("start_time", 0)
            end_ms = utt.get("end_time", 0)
            text = utt.get("text", "")
            speaker = utt.get("additions", {}).get("speaker") if isinstance(utt.get("additions"), dict) else None
            
            start = f"{start_ms//3600000:02d}:{(start_ms%3600000)//60000:02d}:{(start_ms%60000)//1000:02d},{start_ms%1000:03d}"
            end = f"{end_ms//3600000:02d}:{(end_ms%3600000)//60000:02d}:{(end_ms%60000)//1000:02d},{end_ms%1000:03d}"
            
            if speaker:
                text = f"[{speaker}] {text}"
            
            f.write(f"{i}\n{start} --> {end}\n{text}\n\n")

utterances_to_srt(utterances, "$PREFIX.srt")
```

Output: `$PREFIX.srt` with speaker labels and timestamps.

### 3C. whisper.cpp Path (local, privacy-first)

**Convert to 16 kHz mono WAV**:
```bash
ffmpeg -y -i "$PREFIX.<ext>" -ar 16000 -ac 1 -c:a pcm_s16le "$PREFIX.wav"
```

**Transcribe with whisper**:
```bash
whisper-cli \
  -m ~/.local/share/whisper-models/ggml-large-v3-turbo.bin \
  -l <language> \
  -f "$PREFIX.wav" \
  -osrt
```

**Language detection**: If the user specifies a language, use it (e.g., `-l zh` for Chinese, `-l en` for English, `-l ja` for Japanese). If not specified, omit `-l` to let whisper auto-detect.

Output: `$PREFIX.wav.srt` → rename to `$PREFIX.srt`

### 4. Clean up and deliver

- Remove intermediate files (downloaded video, WAV) unless the user asked to keep them.
- Ensure output file is named `$PREFIX.srt`.
- Read the SRT file and display its first 10 subtitle entries (or all if < 10).
- Report: 
  - **Backend used**: whisper.cpp / Douban ASR
  - **Language detected**: (if applicable)
  - **Duration**: audio length in mm:ss
  - **Subtitle entries**: total count
  - **Output file**: path to .srt file
  - **Speakers detected**: (if Douban ASR and speaker info available)

## Output format

Default output is SRT because timestamps are nearly always useful for video content.

### SRT with speaker info (Douban ASR)

If speaker diarization is enabled, each subtitle entry includes the speaker label:
```
1
00:00:00,000 --> 00:00:05,000
[Speaker_1] Hello, welcome to the podcast.

2
00:00:05,500 --> 00:00:10,000
[Speaker_2] Thanks for having me!
```

### Plain text output

If the user explicitly asks for plain text (纯文本 / txt / "just the text"), generate a text version by stripping timestamps and speaker labels:

**Douban ASR**:
```python3
def srt_to_txt(srt_path, txt_path):
    import re
    with open(srt_path, encoding="utf-8") as f:
        content = f.read()
    # Remove: subtitle numbers, timecodes, speaker labels
    text = re.sub(r'^\d+\n', '', content, flags=re.MULTILINE)
    text = re.sub(r'^[\d:,\s]+-->[\d:,\s]+\n', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\[Speaker_\d+\]\s*', '', text, flags=re.MULTILINE)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(text.strip())

srt_to_txt("$PREFIX.srt", "$PREFIX.txt")
```

**whisper.cpp**:
```bash
whisper-cli ... -otxt  # generates $PREFIX.wav.txt → rename to $PREFIX.txt
```

## Notes

- **Credentials**: Douban ASR requires free API credentials. whisper.cpp requires no setup beyond the model download.
- **Accuracy**: Both are high-quality. Douban ASR is faster; whisper.cpp is fully private.
- **Age-restricted content**: For members-only videos, ask the user to provide cookies via `--cookies-from-browser chrome`. Don't attempt to bypass authentication.
- **Platform-specific issues**: Some platforms (Douyin, Xiaohongshu) may require specific cookies or headers. If yt-dlp fails, suggest the user open the video in a browser and retry, or provide cookies.
- **Short clips**: For clips < 5 seconds, accuracy may be lower.
- **Security**: Don't use `--no-check-certificates` or other security-weakening flags.
