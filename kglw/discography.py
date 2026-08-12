"""Build a track -> album index for King Gizzard from MusicBrainz.

The band has an unusually large and fast-moving discography, so the mapping is
fetched from MusicBrainz rather than hand-maintained. The result is cached to
``data/discography.json`` so analysis runs are reproducible and offline.

MusicBrainz asks for <=1 request/second and a descriptive User-Agent; both are
honoured here.

Usage:
    python3 -m kglw.discography            # refresh data/discography.json
    python3 -m kglw.discography --stats     # summarise the cache
"""

from __future__ import annotations

import argparse
import json
import os
import time
import urllib.parse
import urllib.request
from collections import Counter
from typing import Any

ARTIST_MBID = "f58384a4-2ad2-4f24-89c5-c7b74ae1cce7"  # King Gizzard & the Lizard Wizard
API = "https://musicbrainz.org/ws/2"
USER_AGENT = "kglw-history-analysis/0.1 ( https://github.com/skemmis/random_proj )"
RATE_LIMIT_SECONDS = 1.1

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE_PATH = os.path.join(os.path.dirname(HERE), "data", "discography.json")

_last_call = 0.0


def _get(path: str, **params: Any) -> dict:
    """GET a MusicBrainz endpoint, respecting the rate limit."""
    global _last_call
    elapsed = time.monotonic() - _last_call
    if elapsed < RATE_LIMIT_SECONDS:
        time.sleep(RATE_LIMIT_SECONDS - elapsed)

    params.setdefault("fmt", "json")
    url = f"{API}/{path}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                _last_call = time.monotonic()
                return json.load(response)
        except Exception as exc:  # transient 503s are common on this API
            if attempt == 3:
                raise
            wait = 2 ** attempt
            print(f"  retry in {wait}s ({exc})")
            time.sleep(wait)
    raise RuntimeError("unreachable")


def fetch_release_groups() -> list[dict]:
    """All release groups for the artist, paged, with genre tags.

    Genres ride along on this endpoint, so the whole discography's tags cost
    three requests rather than one per release.
    """
    groups, offset = [], 0
    while True:
        page = _get("release-group", artist=ARTIST_MBID, limit=100, offset=offset,
                    inc="genres")
        batch = page.get("release-groups", [])
        groups.extend(batch)
        offset += len(batch)
        if offset >= page.get("release-group-count", 0) or not batch:
            break
        print(f"  fetched {offset} release groups...")
    return groups


def fetch_tracklist(release_group_id: str) -> list[dict]:
    """Track titles and durations from the standard release in a group."""
    data = _get(
        "release",
        **{"release-group": release_group_id, "inc": "recordings", "limit": 25},
    )
    releases = data.get("releases", [])
    if not releases:
        return []

    def track_total(release: dict) -> int:
        return sum(m.get("track-count", 0) for m in release.get("media", []))

    # Pick the *standard* edition, not the longest one: deluxe reissues carry
    # bonus discs and instrumentals that would overstate an album's length and
    # skew any per-track normalisation. The standard edition is the one pressed
    # most often (CD + vinyl + digital), so its track count is the modal one.
    official = [r for r in releases if r.get("status") == "Official"] or releases
    counts = Counter(track_total(r) for r in official if track_total(r))
    if not counts:
        return []
    modal_count = counts.most_common(1)[0][0]
    candidates = [r for r in official if track_total(r) == modal_count]
    best = min(candidates, key=lambda r: r.get("date") or "9999")
    tracks = []
    for medium in best.get("media", []):
        for track in medium.get("tracks", []):
            title = track.get("title")
            if not title:
                continue
            # Track length wins over recording length: the same recording can
            # appear on several releases with different edits.
            length = track.get("length") or (track.get("recording") or {}).get("length")
            tracks.append({"title": title, "length_ms": length})
    return tracks


def build() -> dict:
    print("fetching release groups from MusicBrainz...")
    groups = fetch_release_groups()
    print(f"found {len(groups)} release groups")

    albums = []
    for index, group in enumerate(groups, 1):
        title = group.get("title", "")
        print(f"[{index}/{len(groups)}] {title}")
        try:
            tracks = fetch_tracklist(group["id"])
        except Exception as exc:
            print(f"  !! tracklist failed: {exc}")
            tracks = []
        albums.append(
            {
                "id": group["id"],
                "title": title,
                "first_release_date": group.get("first-release-date", ""),
                "primary_type": group.get("primary-type"),
                "secondary_types": group.get("secondary-types", []),
                "genres": [
                    {"name": g["name"], "count": g.get("count", 0)}
                    for g in sorted(group.get("genres", []),
                                    key=lambda g: -g.get("count", 0))
                ],
                "tracks": tracks,
            }
        )

    return {
        "artist": "King Gizzard & the Lizard Wizard",
        "artist_mbid": ARTIST_MBID,
        "source": "musicbrainz.org",
        "albums": albums,
    }


def load() -> dict:
    with open(CACHE_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--stats", action="store_true", help="summarise the cache")
    ap.add_argument("--genres", action="store_true",
                    help="refresh only the genre tags, merging into the cache")
    args = ap.parse_args(argv)

    if args.stats:
        data = load()
        albums = data["albums"]
        studio = [a for a in albums if a["primary_type"] == "Album" and not a["secondary_types"]]
        print(f"{len(albums)} release groups, {len(studio)} studio albums")
        for album in sorted(studio, key=lambda a: a["first_release_date"]):
            print(f"  {album['first_release_date'][:4]}  {album['title']}  ({len(album['tracks'])} tracks)")
        return 0

    if args.genres:
        # Genres alone are three requests; tracklists are 265. Merge rather
        # than rebuild so a tag refresh stays cheap.
        data = load()
        fresh = {g["id"]: g.get("genres", []) for g in fetch_release_groups()}
        hit = 0
        for album in data["albums"]:
            genres = fresh.get(album["id"])
            if genres:
                album["genres"] = [
                    {"name": g["name"], "count": g.get("count", 0)}
                    for g in sorted(genres, key=lambda g: -g.get("count", 0))
                ]
                hit += 1
        tmp = CACHE_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=1, ensure_ascii=False)
        os.replace(tmp, CACHE_PATH)
        print(f"merged genres into {hit}/{len(data['albums'])} releases")
        return 0

    data = build()
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    # Write-then-rename so a concurrent analysis run never sees a half-file.
    tmp_path = CACHE_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1, ensure_ascii=False)
    os.replace(tmp_path, CACHE_PATH)
    total_tracks = sum(len(a["tracks"]) for a in data["albums"])
    print(f"wrote {CACHE_PATH}: {len(data['albums'])} releases, {total_tracks} tracks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
