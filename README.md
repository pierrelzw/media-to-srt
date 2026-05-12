# media-to-srt

Transcribe a video or audio file (URL or local) into an SRT subtitle file. Choose your transcription engine:

- **🚀 Douban ASR**: Fast cloud-based (ByteDance), supports speaker diarization
- **🔒 whisper.cpp**: Local CPU-based, fully private, no API required

Works with any yt-dlp-compatible platform (YouTube, Bilibili, 小红书, 抖音, Vimeo, Twitter/X, etc.) plus local video and audio files (mp3/m4a/wav/aac/flac/mp4/webm/ogg).

## Install

```bash
claude plugin marketplace add pierrelzw/zhiwei_skills && claude plugin install media-to-srt@pierrelzw --scope user
```

## Prerequisites

### Common (both backends)
```bash
brew install yt-dlp ffmpeg
```

### Option 1: Douban ASR (faster, requires credentials)
1. Get free API credentials: [console.volcengine.com/speech/service/8](https://console.volcengine.com/speech/service/8)
2. Export credentials:
   ```bash
   export DOUBAO_APP_ID="your-app-id"
   export DOUBAO_ACCESS_TOKEN="your-access-token"
   ```

### Option 2: whisper.cpp (local, no credentials)
```bash
brew install whisper-cpp
mkdir -p ~/.local/share/whisper-models
curl -L -o ~/.local/share/whisper-models/ggml-large-v3-turbo.bin \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo.bin
```

See [SKILL.md](SKILL.md) for detailed setup and backend comparison.

## Usage

### English
- `transcribe https://www.youtube.com/watch?v=...`
- `transcribe ./meeting.mp4`
- `transcribe ./voice-memo.mp3`
- `transcribe audio fast` (uses Douban ASR)
- `transcribe offline` (uses whisper.cpp)

### Chinese (中文)
- `转录这个视频 https://www.youtube.com/watch?v=...`
- `转录 ./meeting.mp4`
- `提取字幕 <bilibili url>`
- `播客转文字 ./podcast.wav`
- `快速转录 <url>` (快速 = Douban ASR)
- `离线转录 <url>` (离线 = whisper.cpp)
- `给这个视频生成 SRT，语言是中文`
- `转录并显示说话者信息` (shows speaker labels from Douban)

The skill triggers on: "transcribe a video", "转录视频", "提取字幕", "generate subtitles", "视频转文字", "语音转文字", "转录音频", "转录播客", "播客转文字", "transcribe audio", "transcribe podcast", "voice memo", "快速" (fast), "离线" (offline), or any video/audio URL/path with intent to extract speech.

## Output

- Default: `<prefix>.srt` (timestamps + text, with speaker labels if using Douban ASR)
- Optional plain text: ask for "纯文本" / "txt" / "just the text"
- Optional: ask for speaker timeline / diarization details (Douban ASR only)

## License

MIT
