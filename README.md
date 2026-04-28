# video-to-srt

Transcribe a video (URL or local file) into an SRT subtitle file using whisper.cpp.

Works with any yt-dlp-compatible platform (YouTube, Bilibili, 小红书, 抖音, Vimeo, Twitter/X, etc.) and local video files.

## Install

```bash
claude plugin marketplace add pierrelzw/zhiwei_skills && claude plugin install video-to-srt@pierrelzw --scope user
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

The skill triggers on: "transcribe a video", "转录视频", "提取字幕", "generate subtitles", "视频转文字", "语音转文字", or any video URL/path with intent to extract speech.

## Output

- Default: `<prefix>.srt` (timestamps + text)
- Optional plain text: ask for "纯文本" / "txt" / "just the text"

## License

MIT
