"""Score each album on a heavy <-> light axis from its MusicBrainz genre tags.

"Heavy" and "light" are a judgement call, so the judgement is made once, in
the open, in the keyword tables below — rather than album by album from
memory. Every album's score is then derived the same way and can be audited,
and disagreeing with a result means editing a weight rather than arguing
about a verdict.

Scoring: each genre tag is matched against the longest keyword it contains,
weighted by how many MusicBrainz users voted for that tag, and averaged. The
result runs from -1 (entirely light-tagged) to +1 (entirely heavy-tagged).
Albums whose tags pull both ways land near zero, which is usually correct for
this band — the same record often is both.
"""

from __future__ import annotations

from . import discography

# Weights are "how strongly does this tag imply heavy/light", not "how much do
# I like it". Metal subgenres are unambiguous; rock subgenres are shades.
HEAVY_TAGS = {
    "thrash metal": 1.0, "speed metal": 1.0, "death metal": 1.0,
    "heavy metal": 1.0, "doom metal": 1.0, "sludge metal": 1.0,
    "stoner metal": 1.0, "black metal": 1.0, "progressive metal": 0.9,
    "metal": 0.9, "hardcore": 0.8, "stoner rock": 0.7, "noise rock": 0.7,
    "heavy psych": 0.6, "hard rock": 0.6, "garage punk": 0.6, "punk": 0.6,
    "industrial": 0.5, "occult rock": 0.5, "acid rock": 0.3,
    "garage psych": 0.3, "southern rock": 0.3, "garage rock": 0.25,
    "glam rock": 0.2,
}

LIGHT_TAGS = {
    "easy listening": 1.0, "lounge": 0.9, "soft rock": 0.9, "acoustic": 0.9,
    "bossa nova": 0.9, "folk pop": 0.9, "psychedelic folk": 0.8, "folk": 0.8,
    "ambient": 0.8, "jazz pop": 0.8, "jazz": 0.7, "soul": 0.6, "pop": 0.6,
    "synth-pop": 0.6, "folk rock": 0.6, "jazz-funk": 0.5, "boogie": 0.5,
    "psychedelic pop": 0.5, "progressive pop": 0.5, "indietronica": 0.4,
    "surf": 0.4, "disco": 0.3, "roots rock": 0.3, "space rock": 0.2,
    "jam band": 0.2,
}


def _weight(tag: str, table: dict[str, float]) -> float:
    """Longest matching keyword wins, so 'folk pop' beats bare 'folk'."""
    best, best_len = 0.0, 0
    for keyword, weight in table.items():
        if keyword in tag and len(keyword) > best_len:
            best, best_len = weight, len(keyword)
    return best


# MusicBrainz genre votes for this artist are nearly all 1, so a single
# mistaken tag can carry an album on its own: one user filed the techno EP
# "Made in Timeland" under heavy metal, which was enough to score it heavy off
# two matching tags. Require a few independent tags before trusting a verdict.
MIN_MATCHED_TAGS = 3


def score_album(album: dict) -> float | None:
    """Heaviness in [-1, 1], or None when the tags are too thin to judge."""
    genres = album.get("genres") or []
    total_votes = 0.0
    weighted = 0.0
    matched = 0
    for genre in genres:
        name = genre["name"].lower()
        votes = max(genre.get("count", 0), 1)
        pull = _weight(name, HEAVY_TAGS) - _weight(name, LIGHT_TAGS)
        if pull:
            weighted += votes * pull
            matched += 1
        total_votes += votes
    if not total_votes or matched < MIN_MATCHED_TAGS:
        return None
    return round(weighted / total_votes, 3)


def classify(score: float | None, cutoff: float = 0.08) -> str:
    if score is None:
        return "untagged"
    if score >= cutoff:
        return "heavy"
    if score <= -cutoff:
        return "light"
    return "mixed"


def scores(data: dict | None = None) -> dict[str, dict]:
    """album_id -> {score, band, title} for everything with tags."""
    data = data or discography.load()
    out = {}
    for album in data["albums"]:
        value = score_album(album)
        out[album["id"]] = {
            "score": value,
            "band": classify(value),
            "title": album["title"],
            "year": (album.get("first_release_date") or "")[:4],
            "genres": [g["name"] for g in (album.get("genres") or [])[:5]],
        }
    return out


BANDS = ["heavy", "mixed", "untagged", "light"]

# Diverging, not categorical: heavy and light are two poles of one axis, so
# they take warm/cool opposites with the middle in neutral grey.
BAND_COLOURS = {
    "heavy": ("#e34948", "#e66767"),
    "mixed": ("#898781", "#898781"),
    "untagged": ("#c3c2b7", "#4d4c49"),
    "light": ("#2a78d6", "#3987e5"),
}
BAND_LABELS = {
    "heavy": "Heavy", "light": "Light",
    "mixed": "Mixed", "untagged": "Not tagged",
}


def as_report(report: dict, data: dict | None = None) -> dict:
    """Re-key a minutes report by heaviness band instead of by album.

    The result is report-shaped, so every existing chart view renders it
    without knowing bands exist.
    """
    table = scores(data)
    band_of = {aid: row["band"] for aid, row in table.items()}

    by_month_band: dict[str, dict[str, float]] = {}
    totals: dict[str, float] = {b: 0.0 for b in BANDS}
    for month, albums in report["minutes_by_month_album"].items():
        bucket: dict[str, float] = {}
        for album_id, minutes in albums.items():
            band = band_of.get(album_id, "untagged")
            bucket[band] = bucket.get(band, 0) + minutes
            totals[band] = totals.get(band, 0) + minutes
        by_month_band[month] = bucket

    derived = dict(report)
    derived["minutes_by_month_album"] = by_month_band
    derived["album_titles"] = {b: BAND_LABELS[b] for b in BANDS}
    derived["albums"] = [
        {"album_id": b, "album": BAND_LABELS[b], "minutes": round(totals.get(b, 0), 1),
         "hours": round(totals.get(b, 0) / 60, 2), "distinct_tracks": 0,
         "top_track": None}
        for b in sorted(BANDS, key=lambda b: -totals.get(b, 0))
    ]
    return derived


def main(argv: list[str] | None = None) -> int:
    data = discography.load()
    table = scores(data)
    studio = [
        a for a in data["albums"]
        if a["primary_type"] == "Album" and not a["secondary_types"]
        and table[a["id"]]["score"] is not None
    ]
    studio.sort(key=lambda a: -table[a["id"]]["score"])

    print(f"{'score':>7}  {'band':<7} {'yr':<5} album")
    print("-" * 78)
    for album in studio:
        row = table[album["id"]]
        print(f"{row['score']:>7.2f}  {row['band']:<7} {row['year']:<5} "
              f"{album['title'][:44]}")
        print(f"{'':>7}  {'':<7} {'':<5} {', '.join(row['genres'][:5])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
