# media-to-srt

Transcribe a video or audio file (URL or local) into an SRT subtitle file. Choose your transcription engine:

- **🚀 Douban ASR Flash**: Fast cloud-based (ByteDance), ~5 seconds, supports speaker diarization
- **⚡ Douban ASR Standard**: Reliable async API, handles large files, supports speaker diarization  
- **🔒 whisper.cpp**: Local CPU-based, fully private, no API required, any language

Works with any yt-dlp-compatible platform (YouTube, Bilibili, 小红书, 抖音, Vimeo, Twitter/X, etc.) plus local video and audio files (mp3/m4a/wav/aac/flac/mp4/webm/ogg).

## Install

```bash
claude plugin marketplace add pierrelzw/zhiwei_skills && claude plugin install media-to-srt@pierrelzw --scope user
```

## Prerequisites

### Common (both backends)
```bash
brew install yt-dlp ffmpeg
pip install httpx  # required for Douban ASR
```

### Option 1: Douban ASR (faster, requires credentials)
1. Get free API credentials: [console.volcengine.com/speech/service/8](https://console.volcengine.com/speech/service/8)
2. Store credentials:
   ```bash
   cat > ~/.doubao-config.env << EOF
   DOUBAO_APP_ID=your-app-id
   DOUBAO_ACCESS_TOKEN=your-access-token
   EOF
   chmod 600 ~/.doubao-config.env
   ```

### Option 2: whisper.cpp (local, no credentials)
```bash
brew install whisper-cpp
mkdir -p ~/.local/share/whisper-models
curl -L -o ~/.local/share/whisper-models/ggml-large-v3-turbo.bin \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo.bin
```

See [SKILL.md](SKILL.md) for detailed setup and backend comparison.

## Quick Start

```bash
# Auto-detect backend (Douban Flash if credentials available, else whisper.cpp)
python3 bin/transcribe.py input.mp4

# Force Douban Flash (fastest)
python3 bin/transcribe.py input.mp4 --backend flash

# Force whisper.cpp (local, private)
python3 bin/transcribe.py input.mp4 --backend whisper

# Specify output file
python3 bin/transcribe.py input.mp4 -o subtitles.srt

# Generate both SRT and plain text
python3 bin/transcribe.py input.mp4 --output-txt transcript.txt

# Show speaker timeline (Douban only)
python3 bin/transcribe.py input.mp4 --summary
```

### With Claude

Just ask Claude Code to transcribe:
- `转录这个视频 https://www.youtube.com/watch?v=...`
- `transcribe ./meeting.mp4`
- `提取字幕 <bilibili url>`
- `快速转录 <url>` (uses Douban Flash)
- `离线转录 <url>` (uses whisper.cpp)

The skill triggers on: "transcribe a video", "转录视频", "提取字幕", "generate subtitles", "视频转文字", "语音转文字", "转录音频", "转录播客", "播客转文字", "transcribe audio", "transcribe podcast", "voice memo", or any video/audio URL/path with intent to extract speech.

## Output

- **Default**: `<prefix>.<ext>.srt` (timestamps + text, with speaker labels if Douban)
- **Plain text**: Add `--output-txt file.txt` flag
- **Speaker timeline**: Add `--summary` flag (Douban only)

Example SRT output (Douban ASR with speakers):
```
1
00:00:00,000 --> 00:00:05,000
[Speaker_1] Hello, welcome to the podcast.

2
00:00:05,500 --> 00:00:10,000
[Speaker_2] Thanks for having me!
```

## Architecture

Persistent Python library (not generated each time):
- `lib/config.py` — Credential management
- `lib/doubao_asr.py` — Douban ASR clients (Flash & Standard APIs)
- `lib/srt_converter.py` — Utterances → SRT/TXT conversion
- `bin/transcribe.py` — CLI tool with auto-detection, error handling

All code is version-controlled, testable, and reusable.

## License

MIT
