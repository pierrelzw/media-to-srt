#!/usr/bin/env python3
"""CLI tool to transcribe audio/video files to SRT subtitles."""

import sys
import argparse
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.config import load_credentials, validate_credentials, get_resource_id
from lib.doubao_asr import DoubaoFlashClient, DoubaoStandardClient, DoubaoError
from lib.srt_converter import utterances_to_srt, utterances_to_txt, generate_speaker_summary


def run_doubao(
    audio_path: Path,
    backend: str = "flash",
    output_srt: Optional[Path] = None,
    output_txt: Optional[Path] = None,
    app_id: Optional[str] = None,
    access_token: Optional[str] = None,
    show_summary: bool = False,
) -> int:
    """Run Douban ASR transcription."""

    if not app_id or not access_token:
        app_id, access_token = load_credentials()

    if not validate_credentials(app_id, access_token):
        print("❌ Douban credentials not found")
        print("\nSet up credentials:")
        print("  cat > ~/.doubao-config.env << EOF")
        print("  DOUBAO_APP_ID=your-app-id")
        print("  DOUBAO_ACCESS_TOKEN=your-access-token")
        print("  EOF")
        print("\nOr use environment variables:")
        print("  export DOUBAO_APP_ID=...")
        print("  export DOUBAO_ACCESS_TOKEN=...")
        return 1

    resource_id = get_resource_id(backend)

    print(f"🚀 Using Douban ASR ({backend}) for transcription...")
    print(f"   Input: {audio_path}")

    try:
        if backend == "flash":
            client = DoubaoFlashClient(app_id, access_token, resource_id)
        else:
            client = DoubaoStandardClient(app_id, access_token, resource_id)

        result = client.transcribe(audio_path)

        # Default output path
        if not output_srt:
            output_srt = Path(str(audio_path) + ".srt")

        # Write SRT
        num_srt = utterances_to_srt(result.utterances, output_srt)
        print(f"✅ SRT saved: {output_srt}")

        # Write TXT if requested
        if output_txt:
            num_txt = utterances_to_txt(result.utterances, output_txt)
            print(f"✅ TXT saved: {output_txt}")

        # Print summary
        print(f"\n📊 Transcription Summary:")
        print(f"   Duration: {result.audio_duration_ms / 1000:.1f}s")
        print(f"   Subtitle entries: {len(result.utterances)}")
        print(f"   Wall clock time: {result.wall_clock_s:.1f}s")
        print(f"   Request ID: {result.request_id}")

        if show_summary and result.utterances:
            speakers = {u.get("speaker") for u in result.utterances if u.get("speaker")}
            if speakers and len(speakers) > 1:
                print(f"\n{generate_speaker_summary(result.utterances)}")

        return 0

    except DoubaoError as e:
        print(f"❌ Transcription failed: {e}")
        if e.log_id:
            print(f"   Log ID: {e.log_id}")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


def run_whisper(
    audio_path: Path,
    output_srt: Optional[Path] = None,
    language: Optional[str] = None,
) -> int:
    """Run whisper.cpp transcription."""
    import subprocess

    if not output_srt:
        output_srt = Path(str(audio_path) + ".srt")

    print(f"🔒 Using whisper.cpp (local, offline) for transcription...")
    print(f"   Input: {audio_path}")

    # Convert to 16kHz mono WAV first
    wav_path = Path(str(audio_path).rsplit(".", 1)[0] + ".wav")
    print(f"⏳ Converting to 16kHz mono WAV...")

    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(audio_path),
                "-ar",
                "16000",
                "-ac",
                "1",
                "-c:a",
                "pcm_s16le",
                str(wav_path),
            ],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg conversion failed: {e.stderr.decode()}")
        return 1
    except FileNotFoundError:
        print("❌ ffmpeg not found. Install with: brew install ffmpeg")
        return 1

    # Run whisper
    print(f"⏳ Running whisper transcription...")
    cmd = [
        "whisper-cli",
        "-m",
        str(Path.home() / ".local/share/whisper-models/ggml-large-v3-turbo.bin"),
        "-f",
        str(wav_path),
        "-osrt",
    ]
    if language:
        cmd.extend(["-l", language])

    try:
        subprocess.run(cmd, check=True)
        # Rename output
        srt_from_whisper = Path(str(wav_path) + ".srt")
        srt_from_whisper.rename(output_srt)
        print(f"✅ SRT saved: {output_srt}")

        # Clean up WAV
        wav_path.unlink(missing_ok=True)

        return 0

    except subprocess.CalledProcessError as e:
        print(f"❌ whisper transcription failed")
        return 1
    except FileNotFoundError:
        print("❌ whisper-cli not found. Install with: brew install whisper-cpp")
        return 1


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Transcribe audio/video to SRT subtitles",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-detect backend (Douban if credentials available, else whisper)
  transcribe.py input.mp4

  # Force Douban Flash (fast)
  transcribe.py input.mp4 --backend flash

  # Force whisper.cpp (local, private)
  transcribe.py input.mp4 --backend whisper

  # Specify output file
  transcribe.py input.mp4 --output subtitles.srt

  # Generate both SRT and TXT
  transcribe.py input.mp4 --output-txt transcript.txt
        """,
    )

    parser.add_argument(
        "input",
        type=Path,
        help="Input audio/video file",
    )
    parser.add_argument(
        "-b",
        "--backend",
        choices=["flash", "standard", "whisper", "auto"],
        default="auto",
        help="Transcription backend (default: auto-detect)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output SRT file (default: input.srt)",
    )
    parser.add_argument(
        "--output-txt",
        type=Path,
        help="Also generate plain text file",
    )
    parser.add_argument(
        "-l",
        "--language",
        help="Language code (whisper only, e.g. zh, en, ja)",
    )
    parser.add_argument(
        "--app-id",
        help="Douban app ID (default: from env/config)",
    )
    parser.add_argument(
        "--access-token",
        help="Douban access token (default: from env/config)",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show speaker timeline summary (Douban only)",
    )

    args = parser.parse_args()

    # Validate input
    if not args.input.exists():
        print(f"❌ Input file not found: {args.input}")
        return 1

    # Auto-detect backend
    backend = args.backend
    if backend == "auto":
        app_id, access_token = load_credentials()
        if validate_credentials(app_id, access_token):
            # Use Douban Flash by default if credentials available
            backend = "flash"
        else:
            backend = "whisper"

    print(f"Selected backend: {backend}\n")

    # Run appropriate backend
    if backend == "whisper":
        return run_whisper(args.input, args.output, args.language)
    else:
        return run_doubao(
            args.input,
            backend=backend,
            output_srt=args.output,
            output_txt=args.output_txt,
            app_id=args.app_id,
            access_token=args.access_token,
            show_summary=args.summary,
        )


if __name__ == "__main__":
    sys.exit(main())
