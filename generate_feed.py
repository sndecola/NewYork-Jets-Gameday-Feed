#!/usr/bin/env python3
"""
generate_feed.py

Builds an RSS 2.0 feed of New York Jets gameday scores and stats for the
most recent game, using ESPN's public (unauthenticated) NFL data endpoints.

Output: docs/feed.xml  (served via GitHub Pages once enabled — see README.md)

No API key required. No third-party RSS library required (stdlib only,
plus `requests` for HTTP).
"""

import sys
import datetime
from xml.sax.saxutils import escape

import requests

TEAM_ABBR = "nyj"
TEAM_ID = "20"  # ESPN's internal team id for the Jets
SCHEDULE_URL = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{TEAM_ABBR}/schedule"
SUMMARY_URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary"

OUTPUT_PATH = "docs/feed.xml"
SITE_TITLE = "New York Jets — Gameday Scores & Stats"
SITE_LINK = "https://www.espn.com/nfl/team/_/name/nyj/new-york-jets"
SITE_DESC = "Automated gameday RSS feed: score, final/live status, and key team stats for the most recent New York Jets game."


def fetch_json(url, params=None):
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def get_latest_event():
    """Return the most relevant schedule event: the most recent game that
    has started (in-progress or completed). Falls back to the next
    scheduled game if the season hasn't started yet."""
    data = fetch_json(SCHEDULE_URL)
    events = data.get("events", [])
    if not events:
        raise RuntimeError("No events found in schedule response.")

    started = []
    upcoming = []
    for ev in events:
        comp = ev.get("competitions", [{}])[0]
        status_type = comp.get("status", {}).get("type", {})
        state = status_type.get("state")  # 'pre', 'in', 'post'
        date_str = ev.get("date")
        try:
            ev_date = datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%MZ")
        except (TypeError, ValueError):
            ev_date = None
        if state in ("in", "post"):
            started.append((ev_date, ev))
        else:
            upcoming.append((ev_date, ev))

    if started:
        started.sort(key=lambda x: (x[0] is None, x[0]))
        return started[-1][1]
    if upcoming:
        upcoming.sort(key=lambda x: (x[0] is None, x[0]))
        return upcoming[0][1]

    raise RuntimeError("Could not determine latest or upcoming event.")


def get_summary(event_id):
    return fetch_json(SUMMARY_URL, params={"event": event_id})


def build_score_line(event):
    comp = event.get("competitions", [{}])[0]
    competitors = comp.get("competitors", [])
    status = comp.get("status", {})
    status_type = status.get("type", {})
    state = status_type.get("state")
    detail = status_type.get("detail", "Scheduled")

    home = next((c for c in competitors if c.get("homeAway") == "home"), {})
    away = next((c for c in competitors if c.get("homeAway") == "away"), {})

    home_name = home.get("team", {}).get("displayName", "Home")
    away_name = away.get("team", {}).get("displayName", "Away")
    home_score = home.get("score", "0")
    away_score = away.get("score", "0")

    if state == "pre":
        line = f"{away_name} at {home_name} — {detail}"
    else:
        line = f"{away_name} {away_score} — {home_name} {home_score} ({detail})"

    return line, state


def build_stats_lines(summary):
    """Pull a handful of team stat leaders / box score team stats if present."""
    lines = []
    box = summary.get("boxscore", {})

    teams = box.get("teams", [])
    for team in teams:
        team_name = team.get("team", {}).get("displayName", "Team")
        stats = team.get("statistics", [])
        wanted = {"totalYards", "netPassingYards", "rushingYards", "turnovers", "possessionTime"}
        picked = [s for s in stats if s.get("name") in wanted]
        if picked:
            stat_str = ", ".join(f"{s.get('label', s.get('name'))}: {s.get('displayValue')}" for s in picked)
            lines.append(f"{team_name} — {stat_str}")

    leaders = summary.get("leaders", [])
    for team_leaders in leaders:
        team_name = team_leaders.get("team", {}).get("displayName", "Team")
        for cat in team_leaders.get("leaders", []):
            cat_name = cat.get("displayName", "Leader")
            entries = cat.get("leaders", [])
            if entries:
                top = entries[0]
                athlete = top.get("athlete", {}).get("displayName", "Player")
                val = top.get("displayValue", "")
                lines.append(f"{team_name} {cat_name}: {athlete} ({val})")

    return lines


def build_rss(event, score_line, stat_lines, state):
    game_name = event.get("name", "Jets Game")
    game_date = event.get("date", "")
    try:
        pub_dt = datetime.datetime.strptime(game_date, "%Y-%m-%dT%H:%MZ")
        pub_date_rfc822 = pub_dt.strftime("%a, %d %b %Y %H:%M:%S GMT")
    except (TypeError, ValueError):
        pub_date_rfc822 = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

    status_label = {"pre": "Upcoming", "in": "Live", "post": "Final"}.get(state, "Update")

    description_parts = [f"<b>{escape(status_label)}:</b> {escape(score_line)}"]
    if stat_lines:
        description_parts.append("<br/><b>Key stats:</b><ul>")
        for line in stat_lines:
            description_parts.append(f"<li>{escape(line)}</li>")
        description_parts.append("</ul>")
    description = "".join(description_parts)

    now_rfc822 = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

    item = f"""    <item>
      <title>{escape(f"{status_label}: {score_line}")}</title>
      <link>{escape(SITE_LINK)}</link>
      <guid isPermaLink="false">{escape(event.get('id', game_name))}-{escape(state or '')}</guid>
      <pubDate>{pub_date_rfc822}</pubDate>
      <description><![CDATA[{description}]]></description>
    </item>"""

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>{escape(SITE_TITLE)}</title>
    <link>{escape(SITE_LINK)}</link>
    <description>{escape(SITE_DESC)}</description>
    <language>en-us</language>
    <lastBuildDate>{now_rfc822}</lastBuildDate>
    <ttl>15</ttl>
{item}
  </channel>
</rss>
"""
    return rss


def main():
    try:
        event = get_latest_event()
    except Exception as exc:
        print(f"ERROR fetching schedule: {exc}", file=sys.stderr)
        sys.exit(1)

    score_line, state = build_score_line(event)

    stat_lines = []
    if state in ("in", "post"):
        try:
            summary = get_summary(event.get("id"))
            stat_lines = build_stats_lines(summary)
        except Exception as exc:
            print(f"WARNING: could not fetch boxscore/stats: {exc}", file=sys.stderr)

    rss_xml = build_rss(event, score_line, stat_lines, state)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(rss_xml)

    print(f"Wrote {OUTPUT_PATH}")
    print(score_line)


if __name__ == "__main__":
    main()
