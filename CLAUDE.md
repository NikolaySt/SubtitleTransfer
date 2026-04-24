# SubtitleTransfer

This repo mixes two pipelines around subtitles / transcripts. Source code lives under [src/](src/), one subdirectory per language.

## Repository layout

```text
src/
  python/                              # YouTube transcript bot
    youtube_transcript_bot.py
    requirements.txt
  csharp/                              # Subtitle aligner
    SubtitleTransfer.sln
    SubtitleTransfer/
      Program.cs
      SubtitleTransfer.csproj
      Subtitles/                       # sample .srt inputs
.github/workflows/daily.yml            # scheduled run of the Python bot
.claude/skills/                        # language-specific guidance (python, csharp)
docs/                                  # human-facing docs (GitHub Actions setup, etc.)
outputs/                               # bot-generated (gitignored; retrieved via CI artifact)
README.md                              # user-facing overview
CLAUDE.md                              # this file
```

## Components

- **[src/csharp/SubtitleTransfer/](src/csharp/SubtitleTransfer/)** — C# console app (.NET Core 2.2). Reads paired `.srt` files (foreign + mother tongue), aligns captions by timestamp, and emits aligned CSV and JSON. Entry point: [Program.cs](src/csharp/SubtitleTransfer/Program.cs). Sample inputs live in [src/csharp/SubtitleTransfer/Subtitles/](src/csharp/SubtitleTransfer/Subtitles/) (`<basename>.en.srt` + `<basename>.bg.srt`).
- **[src/python/youtube_transcript_bot.py](src/python/youtube_transcript_bot.py)** — Python CLI. Lists recent videos from a YouTube channel via `yt_dlp`, fetches transcripts via `youtube-transcript-api`, writes clean text / raw JSON / keyword+summary analysis under `outputs/<channel>/<YYYY-MM-DD>/`. Re-runs are idempotent.
- **[.github/workflows/daily.yml](.github/workflows/daily.yml)** — scheduled workflow that runs the Python bot daily and uploads the `outputs/` tree as a downloadable artifact (not committed to the repo).

## Conventions

- Default subtitle languages: `bg` (mother) + `en` (foreign).
- Timestamp alignment tolerance in C#: ±2 seconds ([Program.cs:179-180](src/csharp/SubtitleTransfer/Program.cs#L179-L180)).
- CSV separator is `|` with `#` prefix on timestamp columns.
- Python config precedence: CLI flags > env vars > built-in defaults.
- Bot outputs go to `outputs/` at the repo root (CWD-relative), regardless of where the script lives. Keep that working-directory assumption intact if you move the entry point.

## Running

- Python: `pip install -r src/python/requirements.txt` then `python src/python/youtube_transcript_bot.py --help`. Run from the repo root so `outputs/` lands in the expected place.
- C#: `dotnet run --project src/csharp/SubtitleTransfer` (expects paired `.srt` files in [src/csharp/SubtitleTransfer/Subtitles/](src/csharp/SubtitleTransfer/Subtitles/); change `baseName` in [Program.cs:37](src/csharp/SubtitleTransfer/Program.cs#L37) to pick a set).

## Skills

Language-specific guidance lives under [.claude/skills/](.claude/skills/):
- [python](.claude/skills/python/SKILL.md) — style + deps for the bot.
- [csharp](.claude/skills/csharp/SKILL.md) — style + tooling for the subtitle aligner.
