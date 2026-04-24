"""
Daily YouTube transcript bot.

Lists recent videos from a channel, fetches transcripts in the requested
languages, and writes clean text, raw JSON, and a simple keyword/summary
analysis into <output-root>/<YYYY-MM-DD>/. Re-runs are idempotent: videos
already written for the day are skipped.

Configuration precedence (highest first):
    CLI flags  >  environment variables  >  built-in defaults

Examples
--------
    python youtube_transcript_bot.py
    python youtube_transcript_bot.py --channel-url https://www.youtube.com/@someChannel
    python youtube_transcript_bot.py --channel-url https://www.youtube.com/@x --max-videos 10 --languages bg,en,ru
"""

import argparse
import os
import re
import sys
import json
import datetime as dt
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    reconfigure = getattr(_stream, "reconfigure", None)
    if reconfigure:
        reconfigure(encoding="utf-8", errors="replace")

import yt_dlp
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
)


DEFAULT_CHANNEL_URL = "https://www.youtube.com/@smokescreen8732"
DEFAULT_LANGUAGES = "bg,en"
DEFAULT_MAX_VIDEOS = 5
DEFAULT_OUTPUT_ROOT = "outputs"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Fetch recent YouTube videos from a channel and save transcripts + analysis.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument(
        "--channel-url",
        default=os.environ.get("CHANNEL_URL", DEFAULT_CHANNEL_URL),
        help="Channel URL. Accepts /@handle, /channel/UC..., /c/name, /user/name (with or without /videos).",
    )
    p.add_argument(
        "--max-videos",
        type=int,
        default=int(os.environ.get("MAX_VIDEOS", DEFAULT_MAX_VIDEOS)),
        help="Max recent videos to scan.",
    )
    p.add_argument(
        "--languages",
        default=os.environ.get("LANGUAGES", DEFAULT_LANGUAGES),
        help="Comma-separated transcript language codes, in preference order.",
    )
    p.add_argument(
        "--output-root",
        default=os.environ.get("OUTPUT_ROOT", DEFAULT_OUTPUT_ROOT),
        help="Root directory for outputs. A date subfolder is created inside.",
    )
    return p.parse_args()


def normalize_channel_url(url: str) -> str:
    url = url.strip().rstrip("/")
    if re.search(r"/(?:@[^/]+|channel/[^/]+|c/[^/]+|user/[^/]+)$", url):
        url += "/videos"
    return url


def list_recent_videos(channel_url: str, limit: int) -> list[dict]:
    opts = {
        "quiet": True,
        "skip_download": True,
        "extract_flat": True,
        "playlistend": limit,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(channel_url, download=False)
    return info.get("entries", []) or []


_ytt_api = YouTubeTranscriptApi()


def fetch_transcript(video_id: str, languages: list[str]) -> list[dict] | None:
    try:
        fetched = _ytt_api.fetch(video_id, languages=languages)
    except (TranscriptsDisabled, NoTranscriptFound):
        return None
    except Exception as e:
        print(f"  transcript error for {video_id}: {e}", file=sys.stderr)
        return None
    return fetched.to_raw_data()


def clean_text(segments: list[dict]) -> str:
    raw = " ".join(s["text"] for s in segments)
    raw = re.sub(r"\[.*?\]", " ", raw)
    raw = re.sub(r"\s+", " ", raw).strip()
    return raw


def analyze(text: str) -> dict:
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    summary = " ".join(sentences[:10])
    tokens = re.findall(r"\w+", text.lower(), flags=re.UNICODE)
    keywords = sorted({t for t in tokens if len(t) > 6})[:30]
    return {"summary": summary, "keywords": keywords}


def safe_slug(s: str) -> str:
    s = re.sub(r"[^\w\- ]+", "", s, flags=re.UNICODE)
    s = re.sub(r"\s+", "_", s.strip())
    return s[:80] or "video"


def channel_slug(channel_url: str) -> str:
    m = re.search(r"/(@[^/]+|channel/[^/]+|c/[^/]+|user/[^/]+)", channel_url)
    token = m.group(1) if m else channel_url
    return safe_slug(token.replace("/", "_").lstrip("@"))


def write_outputs(
    day_dir: Path, video_id: str, title: str, segments: list[dict]
) -> bool:
    slug = safe_slug(title)
    base = day_dir / f"{slug}_{video_id}"
    clean_path = base.with_name(base.name + "_clean.txt")
    raw_path = base.with_name(base.name + "_raw.json")
    analysis_path = base.with_name(base.name + "_analysis.txt")

    if clean_path.exists() and analysis_path.exists():
        return False

    day_dir.mkdir(parents=True, exist_ok=True)
    clean = clean_text(segments)

    clean_path.write_text(clean, encoding="utf-8")
    raw_path.write_text(
        json.dumps(segments, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    a = analyze(clean)
    analysis_path.write_text(
        "=== SUMMARY ===\n"
        f"{a['summary']}\n\n"
        "=== KEYWORDS ===\n"
        + ", ".join(a["keywords"])
        + "\n",
        encoding="utf-8",
    )
    return True


def main() -> int:
    args = parse_args()

    channel_url = normalize_channel_url(args.channel_url)
    languages = [code.strip() for code in args.languages.split(",") if code.strip()]
    output_root = Path(args.output_root)
    today = dt.date.today().isoformat()
    day_dir = output_root / channel_slug(channel_url) / today

    print(f"Channel:    {channel_url}")
    print(f"Languages:  {languages}")
    print(f"Max videos: {args.max_videos}")
    print(f"Output:     {day_dir}")

    entries = list_recent_videos(channel_url, args.max_videos)
    if not entries:
        print("No videos found.")
        return 0

    new_count = 0
    for entry in entries:
        video_id = entry.get("id")
        title = entry.get("title") or video_id
        if not video_id:
            continue

        print(f"- {video_id} :: {title}")
        segments = fetch_transcript(video_id, languages)
        if not segments:
            print("  (no transcript available, skipping)")
            continue

        if write_outputs(day_dir, video_id, title, segments):
            print("  saved")
            new_count += 1
        else:
            print("  already processed")

    print(f"Done. New files: {new_count}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
