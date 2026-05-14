"""Douban ASR (Volcengine) clients for Flash and Standard APIs.

References:
- https://openspeech.bytedance.com/api/v3/auc/bigmodel/recognize/flash (Flash)
- https://openspeech.bytedance.com/api/v3/auc/bigmodel/submit (Standard)
"""

import base64
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import httpx


class DoubaoError(Exception):
    """Douban ASR error."""

    def __init__(
        self,
        status_code: str,
        message: str,
        log_id: Optional[str] = None,
    ) -> None:
        super().__init__(f"[{status_code}] {message}")
        self.status_code = status_code
        self.message = message
        self.log_id = log_id


@dataclass
class TranscriptionResult:
    """Transcription result from Douban ASR."""

    text: str
    utterances: list[dict[str, Any]] = field(default_factory=list)
    audio_duration_ms: int = 0
    wall_clock_s: float = 0.0
    request_id: str = ""
    log_id: Optional[str] = None


_FORMAT_BY_SUFFIX = {
    ".wav": "wav",
    ".mp3": "mp3",
    ".m4a": "m4a",
    ".mp4": "mp4",
    ".ogg": "ogg",
    ".flac": "flac",
    ".webm": "webm",
}


def _detect_format(audio_path: Path) -> str:
    """Detect audio format from file extension."""
    suffix = audio_path.suffix.lower()
    fmt = _FORMAT_BY_SUFFIX.get(suffix)
    if fmt is None:
        raise DoubaoError(
            status_code="unsupported_format",
            message=f"Unsupported audio format: {suffix} ({audio_path})",
        )
    return fmt


def _normalize_word(w: dict[str, Any]) -> dict[str, Any]:
    """Normalize word from API response."""
    return {
        "text": w.get("text", ""),
        "start_ms": w.get("start_time", 0),
        "end_ms": w.get("end_time", 0),
        "confidence": w.get("confidence"),
    }


def _normalize_utterance(utt: dict[str, Any]) -> dict[str, Any]:
    """Normalize utterance from API response."""
    additions = utt.get("additions") or {}
    raw_words = utt.get("words") or []
    return {
        "start_ms": utt.get("start_time", 0),
        "end_ms": utt.get("end_time", 0),
        "text": utt.get("text", ""),
        "speaker": additions.get("speaker") if isinstance(additions, dict) else None,
        "words": [_normalize_word(w) for w in raw_words],
    }


class DoubaoFlashClient:
    """Douban ASR Flash API client (single-call, fast)."""

    ENDPOINT = "https://openspeech.bytedance.com/api/v3/auc/bigmodel/recognize/flash"
    SUCCESS_CODE = "20000000"

    def __init__(
        self,
        app_id: str,
        access_token: str,
        resource_id: str = "volc.seedasr.auc",
    ) -> None:
        self.app_id = app_id
        self.access_token = access_token
        self.resource_id = resource_id

    def transcribe(
        self,
        audio_path: str | Path,
        enable_speaker_info: bool = True,
        timeout_s: float = 120.0,
    ) -> TranscriptionResult:
        """Transcribe audio file using Flash API.

        Args:
            audio_path: Path to audio file
            enable_speaker_info: Enable speaker diarization
            timeout_s: Request timeout in seconds

        Returns:
            TranscriptionResult with text, utterances, and metadata

        Raises:
            DoubaoError: If transcription fails
        """
        audio_path = Path(audio_path)
        audio_format = _detect_format(audio_path)

        # Read and encode audio
        raw = audio_path.read_bytes()
        b64 = base64.b64encode(raw).decode("ascii")

        request_id = uuid.uuid4().hex
        headers = {
            "X-Api-App-Key": self.app_id,
            "X-Api-Access-Key": self.access_token,
            "X-Api-Resource-Id": self.resource_id,
            "X-Api-Request-Id": request_id,
            "X-Api-Sequence": "-1",
            "Content-Type": "application/json",
        }

        body = {
            "user": {"uid": self.app_id},
            "audio": {"format": audio_format, "data": b64},
            "request": {
                "model_name": "bigmodel",
                "enable_itn": True,
                "enable_punc": True,
                "show_utterances": True,
                "enable_speaker_info": enable_speaker_info,
            },
        }

        timeout = httpx.Timeout(
            connect=5.0,
            read=timeout_s,
            write=60.0,
            pool=5.0,
        )

        t0 = time.monotonic()
        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.post(self.ENDPOINT, headers=headers, json=body)
        except httpx.HTTPError as e:
            raise DoubaoError(
                status_code="http_error",
                message=f"{type(e).__name__}: {e}",
            ) from e

        wall = time.monotonic() - t0
        log_id = resp.headers.get("X-Tt-Logid")
        api_status = resp.headers.get("X-Api-Status-Code", "")
        api_message = resp.headers.get("X-Api-Message", "")

        if resp.status_code != 200:
            raise DoubaoError(
                status_code=api_status or f"http_{resp.status_code}",
                message=api_message
                or f"HTTP {resp.status_code}: {resp.text[:500]}",
                log_id=log_id,
            )

        if api_status and api_status != self.SUCCESS_CODE:
            raise DoubaoError(
                status_code=api_status,
                message=api_message
                or f"API error; body={resp.text[:500]}",
                log_id=log_id,
            )

        try:
            payload = resp.json()
        except ValueError as e:
            raise DoubaoError(
                status_code="invalid_json",
                message=f"Response body not JSON: {resp.text[:500]}",
                log_id=log_id,
            ) from e

        result_data = payload.get("result") or {}
        audio_info = payload.get("audio_info") or {}
        utterances_raw = result_data.get("utterances") or []
        utterances = [_normalize_utterance(u) for u in utterances_raw]

        return TranscriptionResult(
            text=result_data.get("text", ""),
            utterances=utterances,
            audio_duration_ms=int(audio_info.get("duration", 0)),
            wall_clock_s=wall,
            request_id=request_id,
            log_id=log_id,
        )


class DoubaoStandardClient:
    """Douban ASR Standard API client (synchronous, single call)."""

    ENDPOINT = "https://openspeech.bytedance.com/api/v3/auc/bigmodel/submit"
    SUCCESS_CODE = "20000000"

    def __init__(
        self,
        app_id: str,
        access_token: str,
        resource_id: str = "volc.seedasr.auc",
    ) -> None:
        self.app_id = app_id
        self.access_token = access_token
        self.resource_id = resource_id

    def transcribe(
        self,
        audio_path: str | Path,
        enable_speaker_info: bool = True,
        timeout_s: float = 300.0,
    ) -> TranscriptionResult:
        """Transcribe audio file using Standard API (synchronous).

        Args:
            audio_path: Path to audio file
            enable_speaker_info: Enable speaker diarization
            timeout_s: Request timeout in seconds

        Returns:
            TranscriptionResult with text, utterances, and metadata

        Raises:
            DoubaoError: If transcription fails
        """
        audio_path = Path(audio_path)
        audio_format = _detect_format(audio_path)

        # Read and encode audio
        raw = audio_path.read_bytes()
        b64 = base64.b64encode(raw).decode("ascii")

        request_id = uuid.uuid4().hex
        headers = {
            "X-Api-Key": self.access_token,
            "X-Api-Resource-Id": self.resource_id,
            "X-Api-Request-Id": request_id,
            "Content-Type": "application/json",
        }

        body = {
            "user": {"uid": self.app_id},
            "audio": {"format": audio_format, "data": b64},
            "request": {
                "model_name": "bigmodel",
                "enable_itn": True,
                "enable_punc": True,
                "show_utterances": True,
                "enable_speaker_info": enable_speaker_info,
            },
        }

        timeout = httpx.Timeout(
            connect=5.0,
            read=timeout_s,
            write=60.0,
            pool=5.0,
        )

        t0 = time.monotonic()
        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.post(self.ENDPOINT, headers=headers, json=body)
        except httpx.HTTPError as e:
            raise DoubaoError(
                status_code="http_error",
                message=f"{type(e).__name__}: {e}",
            ) from e

        wall = time.monotonic() - t0
        log_id = resp.headers.get("X-Tt-Logid")
        api_status = resp.headers.get("X-Api-Status-Code", "")
        api_message = resp.headers.get("X-Api-Message", "")

        if resp.status_code != 200:
            raise DoubaoError(
                status_code=api_status or f"http_{resp.status_code}",
                message=api_message or f"HTTP {resp.status_code}: {resp.text[:500]}",
                log_id=log_id,
            )

        if api_status and api_status != self.SUCCESS_CODE:
            raise DoubaoError(
                status_code=api_status,
                message=api_message or f"API error; body={resp.text[:500]}",
                log_id=log_id,
            )

        try:
            payload = resp.json()
        except ValueError as e:
            raise DoubaoError(
                status_code="invalid_json",
                message=f"Response body not JSON: {resp.text[:500]}",
                log_id=log_id,
            ) from e

        result_data = payload.get("result") or {}
        audio_info = payload.get("audio_info") or {}
        utterances_raw = result_data.get("utterances") or []
        utterances = [_normalize_utterance(u) for u in utterances_raw]

        return TranscriptionResult(
            text=result_data.get("text", ""),
            utterances=utterances,
            audio_duration_ms=int(audio_info.get("duration", 0)),
            wall_clock_s=wall,
            request_id=request_id,
            log_id=log_id,
        )
