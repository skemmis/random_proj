"""Total listening time per album, and a month-by-month series.

Watch history records *that* something played, never for how long, so minutes
are reconstructed from MusicBrainz track durations on the stated assumption
that each play ran to completion. Every play is broken into one or more
*segments* -- (album, track, duration) -- so a full-album upload contributes
the whole record and a live medley contributes each track it names.

Music counts, talk does not: concert footage, bootlegs and drum-cams are
listening; interviews, reactions, podcasts and gear rundowns are not.

Usage:
    python3 -m kglw.minutes watch-history.html
    python3 -m kglw.minutes all.jsonl --json minutes.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict

from . import match

# Rows that are people talking about the band rather than the band playing.
NON_MUSIC_MARKERS = (
    "interview", "podcast", "reacts", "reaction", "react to", "explained",
    "review", "unboxing", "tour kit", "rundown", "behind the scenes",
    "documentary", "how to get into", "talking to", "writes a new song",
    "track by track", "breakdown", "q&a", "press conference", "announcement",
    "vinyl community", "record collection", "discography ranked", "tier list",
)

NON_MUSIC_RE = re.compile("|".join(re.escape(m) for m in NON_MUSIC_MARKERS), re.IGNORECASE)


def is_non_music(title: str | None) -> bool:
    return bool(title and NON_MUSIC_RE.search(title))


def segments_for(entry: dict, index: match.AlbumIndex) -> tuple[list[dict], str]:
    """Break one play into (album, track, duration) segments.

    Returns (segments, source) where source explains how duration was derived:
      track      - a single identified track
      album      - a full-album upload, counted as the whole record
      title-scan - track names recovered from a live/medley title
      none       - no duration could be established
    """
    if entry.get("is_full_album") and entry.get("album_id"):
        album = next((a for a in index.albums if a["id"] == entry["album_id"]), None)
        if album:
            segments = [
                {"album_id": album["id"], "album": album["title"], "track": title, "length_ms": length}
                for title, length in match.track_entries(album)
                if length
            ]
            if segments:
                return segments, "album"

    if entry.get("track") and entry.get("album_id"):
        hit = index.by_track.get(match.normalize(entry["track"]))
        length = hit.get("length_ms") if hit else None
        if length:
            return (
                [{
                    "album_id": entry["album_id"],
                    "album": entry["album"],
                    "track": entry["track"],
                    "length_ms": length,
                }],
                "track",
            )

    # Live sets, medleys and drum-cams: recover whatever tracks the title names.
    title = entry.get("title") or ""
    if not is_non_music(title):
        hits = index.find_tracks_in_title(title)
        segments = [
            {
                "album_id": hit["album"]["id"],
                "album": hit["album"]["title"],
                "track": hit["track"],
                "length_ms": hit["length_ms"],
            }
            for hit in hits
            if hit.get("length_ms")
        ]
        if segments:
            return segments, "title-scan"

    return [], "none"


def summarise(entries: list[dict], index: match.AlbumIndex) -> dict:
    by_album: dict[str, dict] = defaultdict(lambda: {"ms": 0, "plays": 0, "tracks": Counter()})
    by_month: Counter = Counter()
    by_month_album: dict[str, Counter] = defaultdict(Counter)
    sources = Counter()
    skipped_non_music = 0
    skipped_unknown: Counter = Counter()
    album_titles: dict[str, str] = {}

    for entry in entries:
        segments, source = segments_for(entry, index)
        sources[source] += 1
        if not segments:
            if is_non_music(entry.get("title")):
                skipped_non_music += 1
            else:
                skipped_unknown[entry.get("title") or "(none)"] += 1
            continue

        stamp = entry.get("watched_at_utc") or entry.get("watched_at_local") or ""
        month = stamp[:7]
        for segment in segments:
            ms = segment["length_ms"]
            album_id = segment["album_id"]
            album_titles[album_id] = segment["album"]
            stats = by_album[album_id]
            stats["ms"] += ms
            stats["tracks"][segment["track"]] += 1
            if month:
                by_month[month] += ms
                by_month_album[month][album_id] += ms
        by_album[segments[0]["album_id"]]["plays"] += 1

    rows = [
        {
            "album_id": album_id,
            "album": album_titles.get(album_id, album_id),
            "minutes": round(stats["ms"] / 60000, 1),
            "hours": round(stats["ms"] / 3600000, 2),
            "plays": stats["plays"],
            "distinct_tracks": len(stats["tracks"]),
            "top_track": stats["tracks"].most_common(1)[0][0] if stats["tracks"] else None,
        }
        for album_id, stats in by_album.items()
    ]
    rows.sort(key=lambda r: -r["minutes"])

    months = sorted(by_month)
    if months:
        # Fill gaps so the chart has no missing columns.
        start_y, start_m = int(months[0][:4]), int(months[0][5:7])
        end_y, end_m = int(months[-1][:4]), int(months[-1][5:7])
        filled = []
        year, mon = start_y, start_m
        while (year, mon) <= (end_y, end_m):
            filled.append(f"{year:04d}-{mon:02d}")
            mon += 1
            if mon == 13:
                year, mon = year + 1, 1
        months = filled

    return {
        "total_minutes": round(sum(r["minutes"] for r in rows), 1),
        "total_hours": round(sum(r["minutes"] for r in rows) / 60, 1),
        "albums": rows,
        "months": months,
        "minutes_by_month": {m: round(by_month.get(m, 0) / 60000, 1) for m in months},
        "minutes_by_month_album": {
            m: {aid: round(ms / 60000, 1) for aid, ms in by_month_album.get(m, {}).items()}
            for m in months
        },
        "album_titles": album_titles,
        "duration_sources": dict(sources),
        "skipped_non_music": skipped_non_music,
        "skipped_unknown_duration": skipped_unknown.most_common(20),
        "skipped_unknown_count": sum(skipped_unknown.values()),
    }


def print_report(report: dict) -> None:
    print(f"\n{'=' * 74}")
    print(f"LISTENING TIME -- {report['total_hours']:,.1f} hours ({report['total_minutes']:,.0f} min)")
    print("=" * 74)
    src = report["duration_sources"]
    print("  duration from: " + ", ".join(f"{k}={v:,}" for k, v in src.items()))
    print(f"  excluded as talk: {report['skipped_non_music']:,} plays; "
          f"no duration available: {report['skipped_unknown_count']:,} plays")

    print(f"\n{'-' * 74}")
    print("ALBUMS BY TOTAL LISTENING TIME")
    print("-" * 74)
    print(f"{'#':>3}  {'album':<46} {'hours':>7} {'min':>8}")
    for rank, row in enumerate(report["albums"][:20], 1):
        print(f"{rank:>3}  {row['album'][:45]:<46} {row['hours']:>7.1f} {row['minutes']:>8,.0f}")

    print(f"\n{'-' * 74}")
    print("MINUTES BY MONTH")
    print("-" * 74)
    series = report["minutes_by_month"]
    peak = max(series.values()) if series else 0
    for month in report["months"]:
        value = series.get(month, 0)
        bar = "#" * int(value / peak * 46) if peak else ""
        print(f"  {month}  {value:>7,.0f}  {bar}")
    print()


def main(argv: list[str] | None = None) -> int:
    from .analyze import load_records

    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("input", help="watch-history.html or parsed .jsonl")
    ap.add_argument("--json", dest="json_out", help="write the report as JSON")
    args = ap.parse_args(argv)

    index = match.load_index()
    records = list(load_records(args.input))
    band_channels, _ = match.find_band_channels(records, index)
    entries = match.classify(records, index, band_channels)
    if not entries:
        print("No King Gizzard records found.", file=sys.stderr)
        return 1

    report = summarise(entries, index)
    print_report(report)

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=1, ensure_ascii=False)
        print(f"wrote {args.json_out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
