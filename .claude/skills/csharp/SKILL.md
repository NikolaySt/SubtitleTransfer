---
name: csharp
description: Guidance for the C# subtitle aligner (SubtitleTransfer project). Apply when editing .cs files or the .csproj in this repo.
---

# C# skill — SubtitleTransfer aligner

Scope: [src/csharp/SubtitleTransfer/](../../../src/csharp/SubtitleTransfer/) — a .NET Core console app that parses paired `.srt` files and emits aligned CSV + JSON.

## Environment

- Target framework: **netcoreapp2.2** (see [SubtitleTransfer.csproj](../../../src/csharp/SubtitleTransfer/SubtitleTransfer.csproj)). This is EOL — flag any proposal to modernize (e.g. to `net8.0`) before rewriting against newer BCL APIs.
- Dependency: `Newtonsoft.Json` 12.0.1. Don't introduce `System.Text.Json` without explicit approval — the target framework predates first-class support.
- Build / run: `dotnet build src/csharp/SubtitleTransfer.sln` and `dotnet run --project src/csharp/SubtitleTransfer`.
- Solution file: [SubtitleTransfer.sln](../../../src/csharp/SubtitleTransfer.sln).

## Domain

- `RowCaption` = one `.srt` cue (`Index`, `From`, `To`, `Text`). See [Program.cs:13-23](../../../src/csharp/SubtitleTransfer/Program.cs#L13-L23).
- `RowTranslation` = pair of `RowCaption` (foreign + mother). See [Program.cs:25-29](../../../src/csharp/SubtitleTransfer/Program.cs#L25-L29).
- Alignment: two cues match if both `From` and `To` differ by **< 2 seconds** ([Program.cs:179-180](../../../src/csharp/SubtitleTransfer/Program.cs#L179-L180)). Don't change this tolerance silently.
- Inputs assumed in [src/csharp/SubtitleTransfer/Subtitles/](../../../src/csharp/SubtitleTransfer/Subtitles/) as `<baseName>.en.srt` + `<baseName>.bg.srt`. `baseName` is hard-coded in `Main` — flag this if refactoring.

## Style (matches existing code)

- Tab indentation, Allman braces (open brace on its own line).
- `private static` helpers in `Program.cs`; no DI, no interfaces — keep it procedural.
- Encoding: `Console.OutputEncoding = Encoding.UTF8` is set in `Main`; preserve this. CSV writer does a `Default → UTF8` byte dance in [Program.cs:214-215](../../../src/csharp/SubtitleTransfer/Program.cs#L214-L215) — investigate before "cleaning up" (it compensates for mixed-encoding `.srt` inputs).

## Output formats (don't break downstream consumers)

- CSV: `<mother>|<foreign>|#<from>|#<to>` with `|` separator and `#` prefix on timestamps.
- JSON: `JsonConvert.SerializeObject(List<RowTranslation>)` — no custom contracts.

## Gotchas

- `ReadAndTransform` drops the **last** caption of the file (it only adds the previous caption when a new index is seen). If you ever fix this, check that existing CSV/JSON diffs are expected.
- Regex for timestamps ignores milliseconds (`\d{2}:\d{2}:\d{2}`). Fine for the ±2s tolerance but worth knowing.
- Multiline caption text is concatenated with a single space ([Program.cs:124](../../../src/csharp/SubtitleTransfer/Program.cs#L124)).
