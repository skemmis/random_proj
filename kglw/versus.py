"""King Gizzard vs Disney: two catalogues, one timeline.

Both sides are measured the same way — plays matched to a track, durations
from that track's release on MusicBrainz, every play assumed to run to
completion. Anything that cannot be given a duration contributes nothing
rather than a guess, on both sides.

Usage:
    python3 -m kglw.versus all.jsonl --json versus.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict

from . import disney, match, minutes


def disney_entries(records: list[dict], index: match.AlbumIndex) -> list[dict]:
    """Annotate Disney rows with the film and track they belong to."""
    entries = []
    for record in records:
        rule = disney.is_disney(record)
        if not rule:
            continue
        title = record.get("title") or ""
        film = disney.film_of(title)
        song = disney.song_title(title)
        hit, how = index.match_track(match.normalize(song))

        entry = dict(record)
        entry["side"] = "disney"
        entry["band_rule"] = rule
        entry["cleaned_title"] = song
        entry["is_full_album"] = False
        entry["is_live"] = False
        if hit:
            entry["album"] = hit["album"]["title"]
            entry["album_id"] = hit["album"]["id"]
            entry["track"] = hit["track"]
            entry["match"] = how
        else:
            entry["album"] = film
            entry["album_id"] = f"disney:{(film or '').lower()}"
            entry["track"] = None
            entry["match"] = "film-only"
        entries.append(entry)
    return entries


def combine(records: list[dict]) -> dict:
    """A minutes report whose two 'albums' are the two catalogues."""
    kglw_index = match.load_index()
    disney_index = match.AlbumIndex(disney.load())

    band_channels, _ = match.find_band_channels(records, kglw_index)
    kglw = match.classify(records, kglw_index, band_channels)
    dis = disney_entries(records, disney_index)

    # A row cannot be both; King Gizzard wins if it somehow matched twice.
    claimed = {id(r) for r in kglw}
    dis = [d for d in dis if id(d) not in claimed]

    by_month: dict[str, dict[str, float]] = defaultdict(dict)
    totals: Counter = Counter()
    plays: Counter = Counter()
    unpriced: Counter = Counter()

    for side, entries, index in (("kglw", kglw, kglw_index),
                                 ("disney", dis, disney_index)):
        for entry in entries:
            segments, source = minutes.segments_for(entry, index)
            stamp = entry.get("watched_at_utc") or entry.get("watched_at_local") or ""
            month = stamp[:7]
            if not segments:
                unpriced[side] += 1
                continue
            plays[side] += 1
            for segment in segments:
                ms = segment["length_ms"]
                totals[side] += ms
                if month:
                    by_month[month][side] = by_month[month].get(side, 0) + ms

    months = sorted(by_month)
    if months:
        start_y, start_m = int(months[0][:4]), int(months[0][5:7])
        end_y, end_m = int(months[-1][:4]), int(months[-1][5:7])
        filled, year, mon = [], start_y, start_m
        while (year, mon) <= (end_y, end_m):
            filled.append(f"{year:04d}-{mon:02d}")
            mon += 1
            if mon == 13:
                year, mon = year + 1, 1
        months = filled

    label = {"kglw": "King Gizzard", "disney": "Disney"}
    return {
        "months": months,
        "minutes_by_month": {
            m: round(sum(by_month.get(m, {}).values()) / 60000, 1) for m in months
        },
        "minutes_by_month_album": {
            m: {s: round(v / 60000, 1) for s, v in by_month.get(m, {}).items()}
            for m in months
        },
        "album_titles": label,
        "albums": [
            {"album_id": s, "album": label[s], "minutes": round(totals[s] / 60000, 1),
             "hours": round(totals[s] / 3600000, 2), "plays": plays[s],
             "distinct_tracks": 0, "top_track": None}
            for s in sorted(label, key=lambda s: -totals[s])
        ],
        "total_minutes": round(sum(totals.values()) / 60000, 1),
        "total_hours": round(sum(totals.values()) / 3600000, 1),
        "plays": dict(plays),
        "unpriced": dict(unpriced),
        "duration_sources": {"track": sum(plays.values()), "none": sum(unpriced.values())},
        "skipped_non_music": 0,
        "skipped_unknown_count": sum(unpriced.values()),
    }


def main(argv: list[str] | None = None) -> int:
    from .analyze import load_records

    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("input", help="watch-history.html or parsed .jsonl")
    ap.add_argument("--json", dest="json_out")
    args = ap.parse_args(argv)

    records = list(load_records(args.input))
    report = combine(records)

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=1, ensure_ascii=False)
        print(f"wrote {args.json_out}", file=sys.stderr)

    print(f"\n{'=' * 66}")
    print(f"KING GIZZARD vs DISNEY — {report['total_hours']:,.1f} hours of music")
    print("=" * 66)
    for row in report["albums"]:
        share = row["minutes"] / max(report["total_minutes"], 1) * 100
        print(f"  {row['album']:<14} {row['hours']:>6.1f} h  {row['minutes']:>7,.0f} min  "
              f"{row['plays']:>5,} plays  {share:>5.1f}%")
    print(f"\n  no duration available: "
          + ", ".join(f"{k}={v:,}" for k, v in report["unpriced"].items()))

    print(f"\n{'-' * 66}")
    print("MINUTES PER MONTH")
    print("-" * 66)
    series = report["minutes_by_month_album"]
    peak = max(report["minutes_by_month"].values(), default=0)
    for month in report["months"]:
        k = series.get(month, {}).get("kglw", 0)
        d = series.get(month, {}).get("disney", 0)
        if not (k or d):
            continue
        bar = "K" * int(k / peak * 40) + "d" * int(d / peak * 40) if peak else ""
        print(f"  {month}  {k:>6.0f} {d:>6.0f}  {bar}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
