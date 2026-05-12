"""Convert ASR utterances to SRT subtitle format."""

from pathlib import Path
from typing import Any, Optional


def ms_to_srt_time(milliseconds: int) -> str:
    """Convert milliseconds to SRT timecode format (HH:MM:SS,mmm).

    Args:
        milliseconds: Time in milliseconds

    Returns:
        SRT timecode string
    """
    total_seconds = milliseconds // 1000
    ms = milliseconds % 1000
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{ms:03d}"


def utterances_to_srt(
    utterances: list[dict[str, Any]],
    output_path: str | Path,
    include_speaker: bool = True,
) -> int:
    """Convert ASR utterances to SRT subtitle file.

    Args:
        utterances: List of utterance dicts from Douban ASR
        output_path: Path to write SRT file
        include_speaker: Include speaker labels if available

    Returns:
        Number of subtitle entries written
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        for i, utt in enumerate(utterances, 1):
            start_ms = utt.get("start_ms", 0)
            end_ms = utt.get("end_ms", 0)
            text = utt.get("text", "").strip()
            speaker = utt.get("speaker")

            if not text:
                continue

            start_time = ms_to_srt_time(start_ms)
            end_time = ms_to_srt_time(end_ms)

            # Add speaker label if available
            if include_speaker and speaker:
                text = f"[{speaker}] {text}"

            # Write SRT entry: index, timecode, text, blank line
            f.write(f"{i}\n")
            f.write(f"{start_time} --> {end_time}\n")
            f.write(f"{text}\n")
            f.write("\n")

    return len(utterances)


def utterances_to_txt(
    utterances: list[dict[str, Any]],
    output_path: str | Path,
    include_speaker: bool = True,
) -> int:
    """Convert ASR utterances to plain text file.

    Args:
        utterances: List of utterance dicts from Douban ASR
        output_path: Path to write text file
        include_speaker: Include speaker labels if available

    Returns:
        Number of entries written
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        for utt in utterances:
            text = utt.get("text", "").strip()
            speaker = utt.get("speaker")

            if not text:
                continue

            if include_speaker and speaker:
                f.write(f"[{speaker}] {text}\n")
            else:
                f.write(f"{text}\n")

    return len(utterances)


def create_speaker_timeline(
    utterances: list[dict[str, Any]],
) -> dict[Optional[str], list[dict[str, Any]]]:
    """Group utterances by speaker.

    Args:
        utterances: List of utterance dicts

    Returns:
        Dict mapping speaker name to list of utterances
    """
    timeline = {}
    for utt in utterances:
        speaker = utt.get("speaker") or "unknown"
        if speaker not in timeline:
            timeline[speaker] = []
        timeline[speaker].append(utt)
    return timeline


def generate_speaker_summary(
    utterances: list[dict[str, Any]],
) -> str:
    """Generate a summary of speakers and their speaking time.

    Args:
        utterances: List of utterance dicts

    Returns:
        Formatted summary string
    """
    timeline = create_speaker_timeline(utterances)

    lines = ["📊 Speaker Timeline:\n"]

    for speaker in sorted(timeline.keys()):
        speaker_utts = timeline[speaker]
        total_ms = sum(u.get("end_ms", 0) - u.get("start_ms", 0) for u in speaker_utts)
        total_chars = sum(len(u.get("text", "")) for u in speaker_utts)
        total_sec = total_ms / 1000

        lines.append(
            f"  {speaker:20s} | {len(speaker_utts):3d} turns | "
            f"{total_sec:6.1f}s | {total_chars:5d} chars"
        )

    return "\n".join(lines)
