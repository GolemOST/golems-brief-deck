"""YouTube transcript ingestion. Wraps youtube-transcript-api with friendly errors."""

import re

from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
)


_VIDEO_ID_RE = re.compile(r"(?:v=|youtu\.be/|/embed/|/shorts/)([A-Za-z0-9_-]{11})")


def extract_video_id(url_or_id: str) -> str:
    """
    Accepts a full YouTube URL or a bare 11-char video ID.
    Raises ValueError if it can't find one.
    """
    s = (url_or_id or "").strip()
    if not s:
        raise ValueError("Empty URL.")
    # Bare ID?
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", s):
        return s
    m = _VIDEO_ID_RE.search(s)
    if m:
        return m.group(1)
    raise ValueError(f"Could not extract a YouTube video ID from: {s!r}")


def fetch_transcript(url_or_id: str, languages=("en",)) -> dict:
    """
    Fetch and flatten a YouTube transcript.

    Returns:
        {
            "video_id": "...",
            "url": "https://www.youtube.com/watch?v=...",
            "text": "full concatenated transcript",
            "char_count": int,
            "segment_count": int,
            "duration_sec": float,
        }

    Raises:
        ValueError                — bad URL / unparseable
        TranscriptsDisabled       — captions disabled on the video
        NoTranscriptFound         — no caption track in requested languages
        RuntimeError              — any other unexpected failure
    """
    video_id = extract_video_id(url_or_id)

    # Try the modern API first (>=0.6); fall back to the classic API.
    segments = []
    try:
        api = YouTubeTranscriptApi()
        result = api.fetch(video_id, languages=list(languages))
        segments = [
            {"text": s.text, "start": s.start, "duration": s.duration}
            for s in result.snippets
        ]
    except (TranscriptsDisabled, NoTranscriptFound):
        raise
    except AttributeError:
        # Older youtube-transcript-api version
        data = YouTubeTranscriptApi.get_transcript(video_id, languages=list(languages))
        segments = [{"text": d["text"], "start": d["start"], "duration": d["duration"]}
                    for d in data]
    except Exception as e:
        raise RuntimeError(f"Unexpected transcript fetch error: {type(e).__name__}: {e}") from e

    if not segments:
        raise RuntimeError("Transcript returned 0 segments.")

    full_text = " ".join(s["text"] for s in segments).strip()
    duration = float(segments[-1]["start"]) + float(segments[-1]["duration"])

    return {
        "video_id": video_id,
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "text": full_text,
        "char_count": len(full_text),
        "segment_count": len(segments),
        "duration_sec": duration,
    }
