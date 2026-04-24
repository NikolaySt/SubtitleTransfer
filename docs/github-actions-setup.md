# GitHub Actions setup — YouTube transcript bot

This repo includes a scheduled workflow at [.github/workflows/daily.yml](../.github/workflows/daily.yml) that runs [src/python/youtube_transcript_bot.py](../src/python/youtube_transcript_bot.py) on a daily cron and uploads the generated `outputs/` tree as a workflow artifact. `outputs/` is **gitignored** — retrieve transcripts from the Actions tab (pick a run → artifact `transcripts-<run_id>`), not from the repo tree.

This doc walks through one-time configuration and day-to-day usage.

---

## 1. Prerequisites

- The repository must live on GitHub (Actions don't run from a local-only git repo).
- You need **write access** to the repo (Admin or Maintain) to enable Actions permissions and create variables.
- Python code + workflow YAML are already in place. You are only configuring GitHub.

---

## 2. Push the repo to GitHub

If it's not already on GitHub:

```bash
gh repo create SubtitleTransfer --private --source=. --remote=origin --push
```

Or via the web UI: create an empty repo on github.com, then:

```bash
git remote add origin https://github.com/<your-user>/SubtitleTransfer.git
git push -u origin master
```

Public repos get unlimited Actions minutes; private repos get ~2000 free minutes/month on the free plan — plenty for a daily 1–3 min job.

---

## 3. Workflow permissions (optional)

Because `outputs/` is gitignored, the workflow's **Commit outputs** step is effectively a no-op (`git add` skips ignored paths) and no push happens — so no elevated permissions are strictly required. The default `GITHUB_TOKEN` is fine.

If you later decide to commit transcripts into the repo, un-ignore `outputs/` in [.gitignore](../.gitignore) and enable write permissions:

1. Repo → **Settings** → **Actions** → **General**
2. Scroll to **Workflow permissions**
3. Select **"Read and write permissions"**
4. Click **Save**

Without both (un-ignore + write permission), the `git push` in the workflow will either fail with a 403 or silently commit nothing.

---

## 4. Configure the channel (and other options)

The bot reads its config in this precedence order:

1. **workflow_dispatch input** (manual run form) — highest
2. **Repo variable** — used by the scheduled cron
3. **Built-in default** in the script (`@smokescreen8732`) — lowest

You almost always want to set a repo variable so the daily cron uses your chosen channel without editing code.

### 4a. Set repo variables

1. Repo → **Settings** → **Secrets and variables** → **Actions** → **Variables** tab
2. Click **New repository variable**
3. Add the variables you want:

| Name          | Example value                                   | Required | Notes                                  |
|---------------|-------------------------------------------------|----------|----------------------------------------|
| `CHANNEL_URL` | `https://www.youtube.com/@smokescreen8732`      | No       | Falls back to script default if unset. |
| `MAX_VIDEOS`  | `5`                                             | No       | Defaults to `5`.                       |
| `LANGUAGES`   | `bg,en`                                         | No       | Comma-separated, preference order.     |

> **Variables vs Secrets**: `CHANNEL_URL` is not sensitive — use Variables (they appear in logs). Use Secrets only for tokens/passwords.

### 4b. Running multiple channels

Either run the workflow multiple times manually (see below, one channel per dispatch), or duplicate the workflow file and point each copy at a different repo variable (e.g. `CHANNEL_URL_A`, `CHANNEL_URL_B`).

---

## 5. Verify with a manual run

Before waiting for the cron:

1. Repo → **Actions** tab
2. Pick **"Daily YouTube Transcript"** from the left sidebar
3. Click **Run workflow** (top-right)
4. Optionally override the channel/max/languages in the form
5. Click the green **Run workflow** button

Watch the run:
- **Run bot** step should log the channel, list videos, and save new ones.
- **Commit outputs** step prints `No new transcripts.` (expected — `outputs/` is gitignored).
- **Upload artifact** step produces a downloadable `transcripts-<run_id>.zip`.

After it finishes, go to the run page → **Artifacts** panel at the bottom → download `transcripts-<run_id>` and extract `outputs/<channel_slug>/<YYYY-MM-DD>/`.

---

## 6. The cron schedule

The schedule line in the workflow:

```yaml
on:
  schedule:
    - cron: "30 20 * * *"
```

### Important facts about GitHub cron

- **Cron time is UTC**, always. GitHub ignores your local timezone.
- `30 20 * * *` = 20:30 UTC = **21:30 Oslo (winter)** / **22:30 Oslo (summer)**.
- Scheduled workflows can be **delayed 5–15 minutes** under load — don't rely on exact timing.
- Schedules pause after **60 days** of repo inactivity; any push resets the clock.
- Only the workflow file on the **default branch** runs on schedule.

### Common cron examples

| When                         | Cron            |
|------------------------------|-----------------|
| Daily at 06:00 UTC           | `0 6 * * *`     |
| Every 6 hours                | `0 */6 * * *`   |
| Weekdays at 08:30 UTC        | `30 8 * * 1-5`  |
| Mondays at midnight UTC      | `0 0 * * 1`     |

Use [crontab.guru](https://crontab.guru) to sanity-check expressions.

To change the schedule, edit the `cron:` line in [.github/workflows/daily.yml](../.github/workflows/daily.yml) and push to the default branch.

---

## 7. Troubleshooting

| Symptom                                                   | Fix                                                                                              |
|-----------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| `Permission to ... denied to github-actions[bot]` on push | Only relevant if you un-ignored `outputs/` to commit files. See Step 3.                          |
| Artifact is empty / missing                               | The bot found no videos or no transcripts for the day; check the **Run bot** log.               |
| `No videos found.`                                        | Channel URL is wrong or private. Test locally: `python src/python/youtube_transcript_bot.py --channel-url …`. |
| `(no transcript available, skipping)` for every video     | Either the channel disables captions, your `LANGUAGES` don't match, or YouTube rate-limited. Wait and retry or add `auto-generated` languages. |
| Workflow doesn't run on schedule                          | Confirm (a) it's on the default branch, (b) repo has had activity in the last 60 days, (c) Actions aren't disabled in Settings → Actions → General. |
| `ModuleNotFoundError: youtube_transcript_api`             | `requirements.txt` wasn't installed — check the **Install dependencies** step log.               |
| Cyrillic titles show as `?` in logs                       | GitHub runners are UTF-8; this is likely only a Windows-local issue. The script forces UTF-8 stdout. |
| Script API error: `YouTubeTranscriptApi has no attribute 'get_transcript'` | `youtube-transcript-api` is too old. `requirements.txt` pins `>=1.2.0`.                         |

### Reading logs

Actions → pick a run → expand the **Run bot** step. The bot prints:

```text
Channel:    https://www.youtube.com/@...
Languages:  ['bg', 'en']
Max videos: 5
Output:     outputs/<slug>/<date>
- <video_id> :: <title>
  saved | already processed | (no transcript available, skipping)
Done. New files: N.
```

### Re-running a failed run

From the run page, click **Re-run all jobs** (or **Re-run failed jobs**). The script is idempotent per day, so re-runs won't duplicate files.

---

## 8. Cost / quota

- **Public repo**: Actions minutes are free and effectively unmetered.
- **Private repo**: 2,000 free minutes/month (Free plan). This bot uses ~1–3 minutes per run × ~30 runs/month ≈ 30–90 minutes/month. Well within the free tier.
- Storage for artifacts counts against 500 MB free; the workflow uploads per-run artifacts that GitHub auto-deletes after 90 days by default.

Check usage at: profile → **Settings** → **Billing and plans** → **Plans and usage**.

---

## 9. Changing the bot or schedule

- **Change the channel for the scheduled run**: edit the `CHANNEL_URL` repo variable (no code change, no commit).
- **Change the time**: edit the `cron:` line and push to the default branch.
- **Change languages for all runs**: set the `LANGUAGES` repo variable (e.g. `bg,en,ru`) or pass per-run via dispatch input.
- **One-off run against a different channel**: use the **Run workflow** button and fill in `channel_url` in the form — no settings change, no commit.

---

## 10. Disabling / pausing

- Temporarily: Actions → pick the workflow → `...` menu → **Disable workflow**.
- Permanently: delete `.github/workflows/daily.yml` and push.
