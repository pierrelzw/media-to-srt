#!/usr/bin/env python3
"""Integration tests for media-to-srt library and CLI."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.config import load_credentials, validate_credentials, get_resource_id
from lib.srt_converter import utterances_to_srt, utterances_to_txt, ms_to_srt_time
from lib.doubao_asr import (
    DoubaoFlashClient,
    DoubaoStandardClient,
    DoubaoError,
    _detect_format,
)


def test_config_loading():
    """Test credential loading from env and config file."""
    print("🧪 Testing credential loading...")

    app_id, token = load_credentials()

    if app_id:
        print(f"  ✅ Found DOUBAO_APP_ID: {app_id[:10]}...")
    else:
        print("  ⚠️  DOUBAO_APP_ID not found (expected if not configured)")

    if token:
        print(f"  ✅ Found DOUBAO_ACCESS_TOKEN: {token[:10]}...")
    else:
        print("  ⚠️  DOUBAO_ACCESS_TOKEN not found (expected if not configured)")

    # Test validation
    is_valid = validate_credentials(app_id, token)
    print(f"  Credentials valid: {is_valid}")

    return app_id, token


def test_resource_ids():
    """Test resource ID resolution."""
    print("\n🧪 Testing resource ID resolution...")

    flash_id = get_resource_id("flash")
    standard_id = get_resource_id("standard")

    print(f"  Flash resource ID: {flash_id}")
    print(f"  Standard resource ID: {standard_id}")

    assert flash_id == "volc.bigasr.auc_turbo", "Flash ID mismatch"
    assert standard_id == "volc.bigasr.auc", "Standard ID mismatch"
    print("  ✅ Resource IDs correct")


def test_format_detection():
    """Test audio format detection."""
    print("\n🧪 Testing audio format detection...")

    test_formats = [
        ("test.wav", "wav"),
        ("test.mp3", "mp3"),
        ("test.m4a", "m4a"),
        ("test.mp4", "mp4"),
        ("test.flac", "flac"),
        ("test.ogg", "ogg"),
        ("test.webm", "webm"),
    ]

    for filename, expected_format in test_formats:
        path = Path(filename)
        detected = _detect_format(path)
        status = "✅" if detected == expected_format else "❌"
        print(f"  {status} {filename}: {detected}")
        assert detected == expected_format, f"Format mismatch for {filename}"


def test_srt_time_conversion():
    """Test milliseconds to SRT time conversion."""
    print("\n🧪 Testing SRT time conversion...")

    test_cases = [
        (0, "00:00:00,000"),
        (1000, "00:00:01,000"),
        (60000, "00:01:00,000"),
        (3600000, "01:00:00,000"),
        (3661234, "01:01:01,234"),
        (12345, "00:00:12,345"),
    ]

    for ms, expected in test_cases:
        result = ms_to_srt_time(ms)
        status = "✅" if result == expected else "❌"
        print(f"  {status} {ms}ms → {result} (expected {expected})")
        assert result == expected, f"Time conversion failed for {ms}"


def test_srt_conversion():
    """Test utterances to SRT conversion."""
    print("\n🧪 Testing SRT conversion...")

    # Mock utterances
    utterances = [
        {
            "start_ms": 0,
            "end_ms": 5000,
            "text": "Hello, world!",
            "speaker": "Speaker_1",
        },
        {
            "start_ms": 5500,
            "end_ms": 10000,
            "text": "This is a test.",
            "speaker": "Speaker_2",
        },
    ]

    output_path = Path("/tmp/test_output.srt")

    try:
        # Convert to SRT
        count = utterances_to_srt(utterances, output_path)
        print(f"  ✅ Created SRT with {count} entries")

        # Verify file was created
        assert output_path.exists(), "SRT file not created"
        content = output_path.read_text()

        # Check content
        assert "[Speaker_1]" in content, "Speaker label missing"
        assert "Hello, world!" in content, "Text missing"
        assert "00:00:00,000 --> 00:00:05,000" in content, "Timecode missing"
        print(f"  ✅ SRT content valid")
        print(f"  ✅ File size: {len(content)} bytes")

        # Also test TXT conversion
        txt_path = Path("/tmp/test_output.txt")
        txt_count = utterances_to_txt(utterances, txt_path)
        assert txt_path.exists(), "TXT file not created"
        print(f"  ✅ Created TXT with {txt_count} entries")

    finally:
        # Cleanup
        output_path.unlink(missing_ok=True)
        txt_path.unlink(missing_ok=True)


def test_cli_imports():
    """Test that CLI tool can be imported."""
    print("\n🧪 Testing CLI imports...")

    try:
        # Add bin to path and import
        bin_path = Path(__file__).parent / "bin"
        sys.path.insert(0, str(bin_path))

        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "transcribe",
            bin_path / "transcribe.py",
        )
        transcribe_module = importlib.util.module_from_spec(spec)

        print("  ✅ CLI tool imports successfully")
        print(f"  ✅ main() function exists: {hasattr(transcribe_module, 'main')}")

    except Exception as e:
        print(f"  ❌ CLI import failed: {e}")
        raise


def test_client_initialization():
    """Test that ASR clients can be initialized."""
    print("\n🧪 Testing ASR client initialization...")

    # Test with dummy credentials
    app_id = "test-app-id"
    token = "test-token"

    try:
        flash_client = DoubaoFlashClient(app_id, token)
        print(f"  ✅ DoubaoFlashClient initialized")
        print(f"     Resource ID: {flash_client.resource_id}")

        standard_client = DoubaoStandardClient(app_id, token)
        print(f"  ✅ DoubaoStandardClient initialized")
        print(f"     Resource ID: {standard_client.resource_id}")

    except Exception as e:
        print(f"  ❌ Client initialization failed: {e}")
        raise


def main():
    """Run all tests."""
    print("=" * 60)
    print("🧪 media-to-srt Integration Tests")
    print("=" * 60)

    try:
        # Config tests
        app_id, token = test_config_loading()
        test_resource_ids()

        # Format detection
        test_format_detection()

        # Time conversion
        test_srt_time_conversion()

        # Conversion
        test_srt_conversion()

        # CLI
        test_cli_imports()

        # Client initialization
        test_client_initialization()

        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)

        if app_id and token:
            print(f"\n🎉 Credentials found! You can now transcribe with:")
            print(f"   python3 bin/transcribe.py <audio-file> --backend flash")
        else:
            print("\n⚠️  No credentials found. Set up ~/.doubao-config.env to use Douban ASR")

        return 0

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
