---
name: media-to-srt
description: Transcribe a video or audio file (URL or local) into an SRT subtitle file using whisper.cpp. Supports any yt-dlp-compatible platform (YouTube, Bilibili, Xiaohongshu/小红书, Douyin/抖音, Vimeo, Twitter/X, etc.) plus local audio files (m4a/mp3/wav/aac/flac). Use this skill whenever the user asks to "transcribe a video", "转录视频", "提取字幕", "generate subtitles", "视频转文字", "get transcript from video", "语音转文字", "转录音频", "转录播客", "播客转文字", "transcribe audio", "transcribe podcast", "voice memo", or provides a video/audio URL or local path (including .m4a/.mp3/.wav) and wants speech-to-text output. This is the right skill even if the user says "转成文本" or just "transcribe" — SRT is the default output because timestamps are almost always useful.
---

# media-to-srt

Transcribe speech from a video or audio file into an SRT subtitle file. Accepts a URL (any platform yt-dlp supports), a local video file, or a local audio file (m4a, mp3, wav, aac, flac, etc.).

## Prerequisites

Check these tools once at the start. If anything is missing, tell the user and suggest the install command — don't silently install. `yt-dlp` is only needed when the input is a URL; local audio/video files skip it.

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

Work in the current project directory by default, or `~/Downloads/` if the user doesn't have a clear project context. Use a sanitized version of the video/audio title or filename as `$PREFIX`.

### 1. Obtain the media

- **URL** (YouTube, Bilibili, 小红书, 抖音, etc.):
  ```bash
  yt-dlp -o "$PREFIX.%(ext)s" "<URL>"
  ```
- **Local video file**: use as-is, set `$PREFIX` from the filename (without extension).
- **Local audio file** (e.g., `.mp3`, `.m4a`, `.wav`, `.aac`, `.flac`): skip yt-dlp entirely. Set `$PREFIX` from the audio filename without its extension and use the file directly as the input to step 2.

### 2. Convert to 16 kHz mono WAV

```bash
ffmpeg -y -i "$PREFIX.<ext>" -ar 16000 -ac 1 -c:a pcm_s16le "$PREFIX.wav"
```

The same ffmpeg command works for both video containers (mp4, mkv, mov, webm, …) and audio files (mp3, m4a, wav, aac, flac, …) — ffmpeg auto-detects the input format and just extracts/resamples the audio stream.

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
- For local audio inputs there's no downloaded video to clean up — only the intermediate `.wav` (and possibly the `.wav.srt` rename) needs handling in step 4.
- Don't use `--no-check-certificates` or other security-weakening flags.
