---
name: video-to-srt
description: Transcribe a video (URL or local file) into an SRT subtitle file using whisper. Supports any yt-dlp-compatible platform (YouTube, Bilibili, Xiaohongshu/小红书, Douyin/抖音, Vimeo, Twitter/X, etc.) and local video files. Use this skill whenever the user asks to "transcribe a video", "转录视频", "提取字幕", "generate subtitles", "视频转文字", "get transcript from video", "语音转文字", or provides a video URL/path and wants speech-to-text output. This is the right skill even if the user says "转成文本" or just "transcribe" — SRT is the default output because timestamps are almost always useful.
---

# video-to-srt

Transcribe speech from a video into an SRT subtitle file. Accepts a URL (any platform yt-dlp supports) or a local video file path.

## Prerequisites

Check these tools once at the start. If anything is missing, tell the user and suggest the install command — don't silently install.

```bash
command -v yt-dlp        # brew install yt-dlp  (only needed for URLs)
command -v ffmpeg        # brew install ffmpeg
command -v whisper-cli   # brew install whisper-cpp
ls ~/.local/share/whisper-models/ggml-large-v3-turbo.bin  # whisper model
```

If the whisper model is missing:

```bash
mkdir -p ~/.local/share/whisper-models
curl -L -o ~/.local/share/whisper-models/ggml-large-v3-turbo.bin \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo.bin
```

## Workflow

Work in the current project directory by default, or `~/Downloads/` if the user doesn't have a clear project context. Use a sanitized version of the video title or filename as `$PREFIX`.

### 1. Obtain the video

- **URL** (YouTube, Bilibili, 小红书, 抖音, etc.):
  ```bash
  yt-dlp -o "$PREFIX.%(ext)s" "<URL>"
  ```
- **Local file**: use as-is, set `$PREFIX` from the filename (without extension).

### 2. Extract audio

```bash
ffmpeg -y -i "$PREFIX.<ext>" -ar 16000 -ac 1 -c:a pcm_s16le "$PREFIX.wav"
```

16 kHz mono PCM is what whisper.cpp expects. Other formats force internal resampling and are slower.

### 3. Transcribe with whisper

```bash
whisper-cli \
  -m ~/.local/share/whisper-models/ggml-large-v3-turbo.bin \
  -l <language> \
  -f "$PREFIX.wav" \
  -osrt
```

**Language detection**: If the user specifies a language, use it (e.g., `-l zh` for Chinese, `-l en` for English, `-l ja` for Japanese). If not specified, omit `-l` to let whisper auto-detect — but mention in the output what language was detected.

Output: `$PREFIX.wav.srt`

### 4. Clean up and deliver

- Remove intermediate files (the downloaded video and WAV) unless the user asked to keep them.
- Rename `$PREFIX.wav.srt` → `$PREFIX.srt` for a cleaner filename.
- Read the SRT file and display its contents to the user.
- Report: language detected, duration, number of subtitle entries, and the output file path.

## Output format

Default output is SRT because timestamps are nearly always useful for video content. If the user explicitly asks for plain text (纯文本 / txt / "just the text"), also generate a plain text version by stripping timestamps:

```bash
whisper-cli ... -otxt  # generates $PREFIX.wav.txt
```

Or run both `-osrt -otxt` in a single pass to produce both formats at once.

## Notes

- For age-restricted or members-only content, ask the user to provide cookies via `--cookies-from-browser chrome`. Don't attempt to bypass authentication.
- Some platforms (Douyin, Xiaohongshu) may require specific cookies or headers. If yt-dlp fails, suggest the user try opening the video in a browser first and then retry, or provide cookies.
- whisper-cli's `large-v3-turbo` model handles Chinese, English, Japanese, Korean, and most major languages well. For very short clips (<5s), accuracy may be lower.
- Don't use `--no-check-certificates` or other security-weakening flags.
