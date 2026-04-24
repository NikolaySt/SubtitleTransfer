---
name: python
description: Guidance for the Python YouTube transcript bot (youtube_transcript_bot.py). Apply when editing Python files in this repo or reasoning about the daily workflow.
---

# Python skill — YouTube transcript bot

Scope: [src/python/youtube_transcript_bot.py](../../../src/python/youtube_transcript_bot.py) and any future Python modules in this repo.

## Environment

- Target Python: **3.10+** (code uses PEP 604 union types like `list[dict] | None`).
- Dependencies pinned in [src/python/requirements.txt](../../../src/python/requirements.txt): `youtube-transcript-api`, `yt-dlp`. No virtualenv committed — install fresh: `pip install -r src/python/requirements.txt`.
- Run locally from the repo root: `python src/python/youtube_transcript_bot.py --help`. The script writes to `outputs/` relative to CWD, so always invoke it from the repo root.
- Scheduled CI: [.github/workflows/daily.yml](../../../.github/workflows/daily.yml) runs the bot daily.

## Style

- **Standard library first.** Use `pathlib.Path`, `argparse`, `json`, `re`. Avoid pulling in `click`, `pydantic`, `requests`, etc. unless there's a real need.
- **Type hints** on function signatures, including the PEP 604 `X | None` form already in use.
- **No logging framework** — the script prints directly to stdout/stderr. Keep it that way for CI log legibility.
- **Idempotent writes.** `write_outputs` skips videos already processed for the day; preserve that guarantee when touching the output path logic.
- **Config precedence**: CLI flag > env var > `DEFAULT_*` constant. Every config option should follow this pattern (see `parse_args`).
- Encode outputs as UTF-8 explicitly (`encoding="utf-8"`) — never rely on platform defaults; CI runs on Linux, dev on Windows.

## Patterns already in use (keep consistent)

- Regex-driven text cleanup (`clean_text`, `safe_slug`) — extend rather than introduce a new NLP dep.
- `yt_dlp.YoutubeDL` with `extract_flat=True` for cheap listing (no download, no per-video API call).
- Transcript errors are caught narrowly (`TranscriptsDisabled`, `NoTranscriptFound`); broad `except Exception` only logs and returns `None`, never crashes the loop.

## When adding features

- New output files: follow the `<slug>_<video_id>_<suffix>` naming pattern under the day dir.
- New languages: pass via `--languages bg,en,ru` (comma-separated); don't hard-code.
- Long-running changes: preserve idempotency — `write_outputs` must be safe to re-run.
