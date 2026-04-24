# SubtitleTransfer

Two small, independent tools around subtitles and transcripts.

| Component | Language | What it does |
|---|---|---|
| [src/python/](src/python/) | Python 3.10+ | Scrapes a YouTube channel, fetches BG/EN transcripts, writes clean text + a keyword/summary analysis into `outputs/<channel>/<date>/`. Runs daily via GitHub Actions. |
| [src/csharp/](src/csharp/) | .NET Core 2.2 (C#) | Takes paired `.srt` files (foreign + mother tongue) and emits aligned CSV and JSON. |

## Repository layout

```text
.
├── src/
│   ├── python/                         # YouTube transcript bot
│   │   ├── youtube_transcript_bot.py
│   │   └── requirements.txt
│   └── csharp/                         # Subtitle aligner
│       ├── SubtitleTransfer.sln
│       └── SubtitleTransfer/
│           ├── Program.cs
│           ├── SubtitleTransfer.csproj
│           └── Subtitles/              # sample .srt inputs
├── .github/workflows/daily.yml         # scheduled run of the Python bot
├── .claude/skills/                     # language-specific assistant guidance
├── docs/
│   └── github-actions-setup.md         # how to configure the scheduled workflow
├── outputs/                            # bot-generated (gitignored; artifact-only in CI)
├── CLAUDE.md
└── README.md
```

## Quick start

All commands assume the repo root as the working directory.

### Python — transcript bot

Requires Python 3.10+.

```bash
pip install -r src/python/requirements.txt
python src/python/youtube_transcript_bot.py --help
```

Run against a channel (overrides the built-in default):

```bash
python src/python/youtube_transcript_bot.py \
  --channel-url https://www.youtube.com/@smokescreen8732 \
  --max-videos 5 \
  --languages bg,en
```

Config precedence: CLI flag > env var (`CHANNEL_URL`, `MAX_VIDEOS`, `LANGUAGES`, `OUTPUT_ROOT`) > built-in default.

Outputs land in `outputs/<channel_slug>/<YYYY-MM-DD>/` as three files per video: `*_clean.txt`, `*_raw.json`, `*_analysis.txt`. Re-runs within the same day are idempotent.

### C# — subtitle aligner

Requires the .NET Core 2.2 SDK (the project targets an EOL framework; modernizing it is a separate discussion).

```bash
dotnet build src/csharp/SubtitleTransfer.sln
dotnet run --project src/csharp/SubtitleTransfer
```

Input files must live in [src/csharp/SubtitleTransfer/Subtitles/](src/csharp/SubtitleTransfer/Subtitles/) as `<baseName>.en.srt` + `<baseName>.bg.srt`. `baseName` is currently hard-coded in [Program.cs:37](src/csharp/SubtitleTransfer/Program.cs#L37).

## Daily automation

[.github/workflows/daily.yml](.github/workflows/daily.yml) runs the Python bot on a daily cron and uploads the resulting `outputs/` tree as a workflow artifact. `outputs/` is gitignored — retrieve transcripts from the **Actions** tab (pick a run → artifact `transcripts-<run_id>`).

For one-time setup (repo permissions, configuring the channel via repo variables, manually triggering a run, troubleshooting) see **[docs/github-actions-setup.md](docs/github-actions-setup.md)**.

## Development notes

- Per-language guidance lives under [.claude/skills/](.claude/skills/) — see [python](.claude/skills/python/SKILL.md) and [csharp](.claude/skills/csharp/SKILL.md).
- Broader repo-wide conventions are in [CLAUDE.md](CLAUDE.md).
- `outputs/` is gitignored — the daily workflow uploads it as a downloadable artifact instead of committing.
