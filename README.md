# media-to-srt

Transcribe a video or audio file (URL or local) into an SRT subtitle file using whisper.cpp.

Works with any yt-dlp-compatible platform (YouTube, Bilibili, 小红书, 抖音, Vimeo, Twitter/X, etc.) plus local video and audio files (mp3/m4a/wav/aac/flac).

## Install

```bash
claude plugin marketplace add pierrelzw/zhiwei_skills && claude plugin install media-to-srt@pierrelzw --scope user
```

## Prerequisites

```bash
brew install yt-dlp ffmpeg whisper-cpp
mkdir -p ~/.local/share/whisper-models
curl -L -o ~/.local/share/whisper-models/ggml-large-v3-turbo.bin \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo.bin
```

## Usage

Just ask Claude:

- `转录这个视频 https://www.youtube.com/watch?v=...`
- `transcribe ./meeting.mp4`
- `提取字幕 <bilibili url>`
- `给这个视频生成 SRT，语言是中文`
- `转录这个播客 ./episode.m4a`
- `transcribe ./voice-memo.mp3`
- `播客转文字 ./podcast.wav`

The skill triggers on: "transcribe a video", "转录视频", "提取字幕", "generate subtitles", "视频转文字", "语音转文字", "转录音频", "转录播客", "播客转文字", "transcribe audio", "transcribe podcast", "voice memo", or any video/audio URL or local path (including .m4a/.mp3/.wav) with intent to extract speech.

## Output

- Default: `<prefix>.srt` (timestamps + text)
- Optional plain text: ask for "纯文本" / "txt" / "just the text"

## License

MIT
