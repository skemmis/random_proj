"""Rank King Gizzard albums by how much of them you actually played.

Accepts either the raw Takeout HTML or a JSONL file produced by
``kglw.parse_history``.

Usage:
    python3 -m kglw.analyze watch-history.html
    python3 -m kglw.analyze watches.jsonl --json report.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict

from . import match, parse_history


def load_records(path: str):
    if path.lower().endswith((".html", ".htm")):
        yield from parse_history.parse_file(path)
        return
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def summarise(entries: list[dict], index: match.AlbumIndex) -> dict:
    # Keyed by MusicBrainz release-group id, never by title: several KGLW
    # albums share a name with a single of the same name ("Fishing for
    # Fishies", "Murder of the Universe"), and collapsing them by title lets a
    # 1-track single stand in for the album -- which produced >100% coverage.
    album_stats: dict[str, dict] = defaultdict(
        lambda: {
            "track_plays": 0,
            "full_album_plays": 0,
            "tracks_played": Counter(),
            "first": None,
            "last": None,
            "live_plays": 0,
        }
    )
    per_year = Counter()
    match_quality = Counter()
    unmatched = Counter()
    channels = Counter()

    for entry in entries:
        match_quality[entry["match"]] += 1
        if entry.get("channel"):
            channels[entry["channel"]] += 1

        stamp = entry.get("watched_at_utc") or entry.get("watched_at_local")
        if stamp:
            per_year[stamp[:4]] += 1

        album_id = entry.get("album_id")
        if album_id is None:
            unmatched[entry.get("title") or "(no title)"] += 1
            continue

        stats = album_stats[album_id]
        if entry.get("is_full_album"):
            stats["full_album_plays"] += 1
        else:
            stats["track_plays"] += 1
            if entry.get("track"):
                stats["tracks_played"][entry["track"]] += 1
        if entry.get("is_live"):
            stats["live_plays"] += 1
        if stamp:
            stats["first"] = min(stats["first"] or stamp, stamp)
            stats["last"] = max(stats["last"] or stamp, stamp)

    albums_by_id = {a["id"]: a for a in index.albums}
    rows = []
    for album_id, stats in album_stats.items():
        album = albums_by_id.get(album_id, {})
        title = album.get("title", album_id)
        total_tracks = len(album.get("tracks") or [])
        # Rough "times through the record": a full-album upload counts as one
        # listen, individual track plays count as the fraction they represent.
        equivalents = stats["full_album_plays"]
        if total_tracks:
            equivalents += stats["track_plays"] / total_tracks
        secondary = album.get("secondary_types") or []
        rows.append(
            {
                "album": title,
                "year": (album.get("first_release_date") or "")[:4],
                "type": album.get("primary_type"),
                "secondary_types": secondary,
                "is_studio_album": album.get("primary_type") == "Album" and not secondary,
                "album_tracks": total_tracks,
                "track_plays": stats["track_plays"],
                "full_album_plays": stats["full_album_plays"],
                "total_plays": stats["track_plays"] + stats["full_album_plays"],
                "distinct_tracks_played": len(stats["tracks_played"]),
                "coverage": (len(stats["tracks_played"]) / total_tracks) if total_tracks else None,
                "album_equivalents": round(equivalents, 2),
                "live_plays": stats["live_plays"],
                "first_played": stats["first"],
                "last_played": stats["last"],
                "top_tracks": stats["tracks_played"].most_common(5),
            }
        )

    rows.sort(key=lambda r: (-r["total_plays"], r["album"]))
    return {
        "total_kglw_plays": len(entries),
        "albums": rows,
        "per_year": dict(sorted(per_year.items())),
        "match_quality": dict(match_quality.most_common()),
        "top_unmatched": unmatched.most_common(25),
        "top_channels": channels.most_common(10),
    }


def print_report(report: dict) -> None:
    total = report["total_kglw_plays"]
    print(f"\n{'=' * 78}")
    print(f"KING GIZZARD & THE LIZARD WIZARD -- {total:,} plays in watch history")
    print("=" * 78)

    quality = report["match_quality"]
    matched = total - quality.get("unmatched", 0)
    pct = (matched / total * 100) if total else 0
    print(f"\nAttributed to an album: {matched:,}/{total:,} ({pct:.1f}%)")
    print("  by rule: " + ", ".join(f"{k}={v:,}" for k, v in quality.items()))

    print(f"\n{'-' * 78}")
    print("ALBUMS BY TOTAL PLAYS")
    print("-" * 78)
    header = f"{'#':>3}  {'album':<44} {'yr':<5} {'plays':>6} {'trk':>5} {'cov':>6}"
    print(header)
    for rank, row in enumerate(report["albums"][:25], 1):
        title = row["album"][:43]
        coverage = f"{row['coverage']*100:.0f}%" if row["coverage"] is not None else "-"
        played = f"{row['distinct_tracks_played']}/{row['album_tracks']}"
        print(
            f"{rank:>3}  {title:<44} {row['year']:<5} {row['total_plays']:>6} "
            f"{played:>5} {coverage:>6}"
        )

    print(f"\n{'-' * 78}")
    print("STUDIO ALBUMS BY ESTIMATED TIMES PLAYED THROUGH")
    print("(track plays / album length, plus full-album uploads)")
    print("-" * 78)
    # Singles and EPs are excluded here: dividing a few plays by a 1-2 track
    # release yields huge "times through" numbers that drown out real albums.
    studio = [r for r in report["albums"] if r["is_studio_album"] and r["album_tracks"] >= 5]
    by_equiv = sorted(studio, key=lambda r: -r["album_equivalents"])
    for rank, row in enumerate(by_equiv[:15], 1):
        print(f"{rank:>3}  {row['album'][:52]:<54} {row['album_equivalents']:>8.2f}")

    if report["per_year"]:
        print(f"\n{'-' * 78}")
        print("PLAYS PER YEAR")
        print("-" * 78)
        peak = max(report["per_year"].values())
        for year, count in report["per_year"].items():
            bar = "#" * int(count / peak * 44) if peak else ""
            print(f"  {year}  {count:>6}  {bar}")

    if report["top_unmatched"]:
        print(f"\n{'-' * 78}")
        print("TOP UNATTRIBUTED TITLES (live sets, interviews, fan edits)")
        print("-" * 78)
        for title, count in report["top_unmatched"][:15]:
            print(f"  {count:>5}  {title[:66]}")

    print()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("input", help="watch-history.html or parsed .jsonl")
    ap.add_argument("--json", dest="json_out", help="also write the report as JSON")
    ap.add_argument("--dump", help="write matched KGLW records as JSONL")
    args = ap.parse_args(argv)

    index = match.load_index()
    records = list(load_records(args.input))
    band_channels, borderline = match.find_band_channels(records, index)
    print(
        f"scanned {len(records):,} records; "
        f"{len(band_channels)} KGLW channels identified "
        f"({len(borderline)} borderline, excluded)",
        file=sys.stderr,
    )
    entries = match.classify(records, index, band_channels)

    if not entries:
        print("No King Gizzard records found.", file=sys.stderr)
        return 1

    if args.dump:
        with open(args.dump, "w", encoding="utf-8") as fh:
            for entry in entries:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    report = summarise(entries, index)
    print_report(report)

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=1, ensure_ascii=False)
        print(f"wrote {args.json_out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
