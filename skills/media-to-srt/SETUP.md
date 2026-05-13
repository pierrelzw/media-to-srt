# Setup Guide for media-to-srt

## One-time Setup

### 1. Install Dependencies

```bash
cd media-to-srt

# Create virtual environment
python3 -m venv .venv

# Activate venv
source .venv/bin/activate

# Install httpx (required for Douban ASR)
pip install httpx

# Also install for local whisper.cpp use
brew install ffmpeg whisper-cpp yt-dlp

# Download whisper model (~3GB)
mkdir -p ~/.local/share/whisper-models
curl -L -o ~/.local/share/whisper-models/ggml-large-v3-turbo.bin \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo.bin
```

### 2. Configure Douban ASR (Optional but Recommended)

Get free API credentials from [console.volcengine.com/speech/service/8](https://console.volcengine.com/speech/service/8)

Store credentials in `~/.doubao-config.env`:

```bash
cat > ~/.doubao-config.env << EOF
DOUBAO_APP_ID=your-app-id
DOUBAO_ACCESS_TOKEN=your-access-token
EOF

chmod 600 ~/.doubao-config.env
```

Or use environment variables:

```bash
export DOUBAO_APP_ID=your-app-id
export DOUBAO_ACCESS_TOKEN=your-access-token
```

### 3. Verify Setup

Run integration tests:

```bash
source .venv/bin/activate
python3 test_integration.py
```

Expected output:

```
🎉 Credentials found! You can now transcribe with:
   python3 bin/transcribe.py <audio-file> --backend flash
```

## Usage

### Activate Virtual Environment

Every session, activate the venv:

```bash
cd media-to-srt
source .venv/bin/activate
```

### Basic Usage

```bash
# Auto-detect backend (Douban Flash if credentials available, else whisper)
python3 bin/transcribe.py input.mp4

# Specific backend
python3 bin/transcribe.py input.mp4 --backend flash      # Fast (~5 sec)
python3 bin/transcribe.py input.mp4 --backend standard   # Large files
python3 bin/transcribe.py input.mp4 --backend whisper    # Offline

# Generate both SRT and TXT
python3 bin/transcribe.py input.mp4 --output-txt transcript.txt

# Show speaker timeline (Douban only)
python3 bin/transcribe.py input.mp4 --summary

# Specify language (whisper only)
python3 bin/transcribe.py input.mp4 --backend whisper -l zh
```

### With Claude Code

```bash
# In Claude Code, just ask:
# "转录这个视频 <url>"
# "快速转录 <url>"  (uses Douban Flash)
# "离线转录 <url>"  (uses whisper.cpp)
```

## Architecture

```
lib/
├── config.py          # Credential management (env vars + ~/.doubao-config.env)
├── doubao_asr.py      # Douban ASR Flash & Standard clients
├── srt_converter.py   # Utterances → SRT/TXT conversion
└── __init__.py        # Package exports

bin/
└── transcribe.py      # CLI tool with auto-detection & error handling
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'httpx'"

Solution: Activate venv and install httpx:

```bash
source .venv/bin/activate
pip install httpx
```

### "DOUBAO_APP_ID not found"

Solution: Create `~/.doubao-config.env` or set environment variables:

```bash
export DOUBAO_APP_ID=your-app-id
export DOUBAO_ACCESS_TOKEN=your-access-token
```

### "whisper-cli not found"

Solution: Install whisper.cpp:

```bash
brew install whisper-cpp
```

### File size/format errors

Supported audio formats: wav, mp3, m4a, mp4, flac, ogg, webm

Max file size:
- Douban Flash: 100 MB
- Douban Standard: Unlimited
- whisper.cpp: Unlimited

## Testing

Run integration tests to verify everything works:

```bash
python3 test_integration.py
```

Tests cover:
- Credential loading (env + config file)
- Resource ID resolution
- Audio format detection (7 formats)
- SRT time conversion
- SRT/TXT file generation
- ASR client initialization
- CLI tool import

## Notes

- Credentials are **never logged** (loaded securely from env/file)
- All code is **persistent and version-controlled** (not generated each time)
- Supports **three backends**: Flash (fast), Standard (reliable), whisper.cpp (offline)
- **Speaker diarization** supported on Douban backends
- **Automatic backend selection** based on credentials + file size
