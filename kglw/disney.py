"""Identify Disney soundtrack listening and give it durations.

Disney is not an artist, it is a catalogue: dozens of soundtracks by different
performers. The reliable signal is YouTube Music's own convention — soundtrack
tracks are titled ``Song (From "Film"/Soundtrack Version)`` — which names the
film directly. Films are then filtered against the Disney canon below.

Durations come from the same place as the King Gizzard ones: the film's
soundtrack release on MusicBrainz, cached in the same shape as
``data/discography.json`` so the existing matcher and minutes pipeline read it
without modification.

Usage:
    python3 -m kglw.disney                 # build data/disney.json
    python3 -m kglw.disney --films         # show the canon and what was found
"""

from __future__ import annotations

import argparse
import json
import os
import re

from . import discography

CACHE_PATH = os.path.join(os.path.dirname(discography.CACHE_PATH), "disney.json")

# Walt Disney Pictures / Animation / Pixar releases. Deliberately excludes the
# 20th Century Fox catalogue Disney bought in 2019 (Home Alone, Walter Mitty)
# and the pre-acquisition Muppet films: "Disney songs" means the Disney canon,
# not everything Disney now owns. Titles are matched case-insensitively
# against the film named in the video title.
DISNEY_FILMS = {
    "frozen", "frozen 2", "frozen ii", "olaf's frozen adventure",
    "tangled", "mary poppins", "mary poppins returns",
    "the little mermaid", "the lion king", "sleeping beauty", "moana",
    "moana 2", "alice in wonderland", "cinderella", "the jungle book",
    "aladdin", "the princess and the frog", "toy story", "toy story 2",
    "toy story 3", "toy story 4", "lilo & stitch", "pocahontas", "brave",
    "tarzan", "lava", "turning red", "mulan", "snow white and the seven dwarfs",
    "treasure planet", "encanto", "coco", "up", "wall-e", "ratatouille",
    "monsters, inc.", "finding nemo", "finding dory", "the incredibles",
    "incredibles 2", "inside out", "inside out 2", "zootopia", "wreck-it ralph",
    "ralph breaks the internet", "big hero 6", "raya and the last dragon",
    "luca", "soul", "onward", "the aristocats", "robin hood", "dumbo",
    "bambi", "peter pan", "lady and the tramp", "101 dalmatians",
    "the sword in the stone", "the rescuers", "oliver & company",
    "beauty and the beast", "hercules", "atlantis: the lost empire",
    "the emperor's new groove", "chicken little", "bolt", "the hunchback of notre dame",
    "a bug's life", "cars", "cars 2", "cars 3", "wish", "strange world",
    "pirates of the caribbean", "marvel rising", "descendants", "high school musical",
    "the muppets", "hocus pocus", "the nightmare before christmas",
    "james and the giant peach", "fantasia", "song of the south",
    "the fox and the hound", "the great mouse detective", "pete's dragon",
}

# The film name inside the title, e.g. Let It Go (From "Frozen"/Single Version)
FROM_RE = re.compile(r'\(From ["“]([^"”]+)["”]?', re.IGNORECASE)
# Everything after the song name: (From ...), (Soundtrack Version), [Official]
SUFFIX_RE = re.compile(
    r'\s*[\(\[](?:from|feat|featuring|soundtrack|single|album|original|official|'
    r'karaoke|instrumental|sing[- ]?along|score|end title|reprise\)?$)[^\)\]]*[\)\]]',
    re.IGNORECASE,
)


def film_of(title: str | None) -> str | None:
    """The film a soundtrack title names, or None."""
    if not title:
        return None
    match = FROM_RE.search(title)
    if not match:
        return None
    film = match.group(1)
    # Some YouTube titles lose the closing quote: 'Let It Go (From "Frozen /
    # Single Version)' captures the qualifier along with the film, so cut at
    # the separator and drop any trailing bracket.
    film = film.split("/")[0]
    return film.strip().rstrip('")').strip()


def is_disney_film(film: str | None) -> bool:
    if not film:
        return False
    name = film.lower().strip()
    if name in DISNEY_FILMS:
        return True
    # "Pirates of the Caribbean: At World's End" -> match the series prefix.
    head = name.split(":")[0].strip()
    return head in DISNEY_FILMS


def song_title(title: str) -> str:
    """Strip the soundtrack furniture, leaving the song name."""
    cleaned = SUFFIX_RE.sub("", title)
    # A trailing unmatched "(From ..." with no closing bracket.
    cleaned = re.sub(r'\s*\(From ["“].*$', "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip(" -–—")


def is_disney(record: dict) -> str | None:
    """Return the rule that marks this record as Disney, else None."""
    film = film_of(record.get("title"))
    if is_disney_film(film):
        return "film-tag"
    channel = (record.get("channel") or "").lower()
    if "disney" in channel or "pixar" in channel:
        return "channel"
    return None


def _tracklist(release_id: str) -> list[dict]:
    detail = discography._get(f"release/{release_id}", inc="recordings")
    tracks = []
    for medium in detail.get("media", []):
        for track in medium.get("tracks", []):
            name = track.get("title")
            length = track.get("length") or (track.get("recording") or {}).get("length")
            if name:
                tracks.append({"title": name, "length_ms": length})
    return tracks


def _key(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()


def fetch_soundtrack(film: str, wanted: set[str] | None = None,
                     candidates: int = 5) -> list[dict]:
    """Song -> duration for a film, merged across its soundtrack releases.

    MusicBrainz carries many releases per film -- single-disc, deluxe, score,
    karaoke -- and their titles do not tell them apart. Choosing one is the
    wrong problem: what is needed is a title-to-duration lookup, not a
    canonical album. So the candidates' tracklists are merged. A single-disc
    Frozen misses the score cues, the score misses the songs, and the union
    covers both, which is what someone playing the deluxe edition listened to.
    Durations for the same song barely differ between editions, so the first
    one seen wins.
    """
    found = discography._get(
        "release", query=f'release:"{film}" AND type:soundtrack', limit=12
    )
    releases = found.get("releases", [])
    if not releases:
        return []

    merged: dict[str, dict] = {}
    seen: set[str] = set()
    for release in releases:
        if release["id"] in seen or len(seen) >= candidates:
            continue
        seen.add(release["id"])
        try:
            tracks = _tracklist(release["id"])
        except Exception:
            continue
        for track in tracks:
            key = _key(track["title"])
            if key and key not in merged and track.get("length_ms"):
                merged[key] = track
        if wanted and sum(1 for w in wanted if w in merged) >= len(wanted):
            break
    return list(merged.values())


def build(films: list[str], wanted: dict[str, set[str]] | None = None) -> dict:
    albums = []
    for index, film in enumerate(films, 1):
        print(f"[{index}/{len(films)}] {film}", end=" ")
        try:
            tracks = fetch_soundtrack(film, (wanted or {}).get(film))
        except Exception as exc:
            print(f"  !! {exc}")
            tracks = []
        have = {_key(t["title"]) for t in tracks}
        need = (wanted or {}).get(film) or set()
        hit = sum(1 for w in need if w in have)
        print(f"-> {len(tracks)} tracks, covers {hit}/{len(need)} played songs")
        if not tracks:
            print("  (no soundtrack found)")
        albums.append({
            "id": f"disney:{film.lower()}",
            "title": film,
            "first_release_date": "",
            "primary_type": "Album",
            "secondary_types": [],
            "genres": [],
            "tracks": tracks,
        })
    return {"artist": "Disney", "source": "musicbrainz.org", "albums": albums}


def load() -> dict:
    with open(CACHE_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--films", nargs="*", help="films to fetch (default: from history)")
    ap.add_argument("--from-history", help="a parsed .jsonl to take the film list from")
    args = ap.parse_args(argv)

    films = args.films or []
    if args.from_history:
        counts: dict[str, int] = {}
        wanted: dict[str, set[str]] = {}
        with open(args.from_history, "r", encoding="utf-8") as fh:
            for line in fh:
                record = json.loads(line)
                film = film_of(record.get("title"))
                if is_disney_film(film):
                    counts[film] = counts.get(film, 0) + 1
                    wanted.setdefault(film, set()).add(
                        _key(song_title(record.get("title") or ""))
                    )
        films = [f for f, _ in sorted(counts.items(), key=lambda kv: -kv[1])]
        print(f"{len(films)} Disney films in history: "
              + ", ".join(f"{f} ({counts[f]})" for f in films[:12]))

    if not films:
        print("nothing to fetch; pass --films or --from-history")
        return 1

    data = build(films, locals().get("wanted"))
    tmp = CACHE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1, ensure_ascii=False)
    os.replace(tmp, CACHE_PATH)
    total = sum(len(a["tracks"]) for a in data["albums"])
    print(f"wrote {CACHE_PATH}: {len(data['albums'])} soundtracks, {total} tracks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
