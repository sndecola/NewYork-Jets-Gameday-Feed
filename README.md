# Jets Gameday RSS

An RSS feed of **New York Jets gameday scores and stats**, auto-updated for the most current/recent game. Data comes from ESPN's public NFL endpoints (no API key needed).

- `scripts/generate_feed.py` — pulls the latest Jets game (live or final) plus key box-score stats and writes `docs/feed.xml`
- `docs/feed.xml` — the actual feed, served via GitHub Pages. Already includes a real sample item (Packers 20‑17 Jets, OT, Sep 20, 2026) so it works before you even run the script.
- `.github/workflows/update-feed.yml` — GitHub Action that reruns the script automatically and commits the refreshed feed

## 1. Create the repo

You're already signed into GitHub, so:

1. Go to https://github.com/new
2. Repository name: `jets-gameday-rss` (or whatever you like)
3. Keep it **Public** (required for free GitHub Pages)
4. Click **Create repository**

## 2. Upload these files

Easiest path — no git command line needed:

1. On your new repo's page, click **Add file → Upload files**
2. Drag in this whole folder structure (keep `scripts/`, `docs/`, `.github/workflows/`, `requirements.txt`, `README.md`)
3. Commit directly to `main`

(If you're comfortable with git locally instead: `git clone`, copy these files in, `git add . && git commit -m "Initial commit" && git push`.)

## 3. Turn on GitHub Pages (this gives you the public feed URL)

1. In your repo: **Settings → Pages**
2. Under "Build and deployment" → Source: **Deploy from a branch**
3. Branch: `main`, folder: `/docs` → **Save**
4. After ~1 minute, your feed will be live at:

   ```
   https://<your-username>.github.io/jets-gameday-rss/feed.xml
   ```

   That URL is what you paste into any RSS reader (Feedly, NetNewsWire, Inoreader, etc.).

## 4. Turn on the auto-update Action

The workflow file is already included and needs no setup — GitHub Actions is on by default for repos with a `.github/workflows/` file. Just confirm it's enabled:

1. **Settings → Actions → General** → make sure "Allow all actions" is selected
2. Go to the **Actions** tab → you should see "Update Jets Gameday RSS Feed"
3. Click **Run workflow** once manually to test it immediately, rather than waiting for the schedule

By default it runs:
- Every 20 minutes on Sundays (UTC) — loosely covers live Sunday games
- Once a day at 13:00 UTC — catches schedule changes, bye weeks, next-opponent updates

**Note on schedule:** cron times are UTC and GitHub may delay scheduled runs by a few minutes during high load. If the Jets play a Monday or Thursday night game, edit `.github/workflows/update-feed.yml` and add a cron line for that day, e.g.:

```yaml
- cron: "*/20 * * * 1"   # Mondays
- cron: "*/20 * * * 4"   # Thursdays
```

## 5. Run it locally (optional, to test before pushing)

```bash
pip install -r requirements.txt
python scripts/generate_feed.py
```

This overwrites `docs/feed.xml` with the current latest-game data.

## How it works

`generate_feed.py`:
1. Fetches the Jets' schedule from ESPN's public schedule endpoint
2. Picks the most recent game that has started (live or final) — or the next upcoming one if the season hasn't started
3. If the game is live or final, fetches the box score/leaders summary for that specific game
4. Builds a single-item RSS 2.0 feed with the score line and a bulleted list of key stats (yardage, turnovers, top performers)
5. Writes it to `docs/feed.xml`

The feed intentionally keeps **one current item** rather than a growing history — each run reflects "the most current game." If you'd rather keep a running history of past games as separate items, let me know and I can adjust the script to append instead of overwrite.

## Troubleshooting

- **Feed shows old data:** re-run the Action manually (Actions tab → Run workflow), or check that the schedule endpoint didn't change shape (ESPN's public API is unofficial and can change without notice).
- **Pages URL 404s:** double check Settings → Pages source is `main` / `/docs`, and give it a minute after the first push.
- **Action fails to push:** check Settings → Actions → General → Workflow permissions is set to "Read and write permissions."
