"""Identify King Gizzard watches and attribute them to a track and album.

Two separate problems, kept separate on purpose:

1. *Is this the band at all?* Decided from the channel name or an explicit
   mention in the video title. Bare track titles on unrelated channels are NOT
   claimed -- several KGLW songs ("The River", "Work This Time") have titles
   generic enough to produce false positives.

2. *Which album is it?* Matched against the MusicBrainz tracklist index, with
   studio albums preferred when a track appears on several releases.

Every record carries the rule that classified it so results can be audited.
"""

from __future__ import annotations

import difflib
import html
import re
from typing import Iterable

from . import discography

BAND_TITLE_PATTERNS = [
    "king gizzard",
    "lizard wizard",
    "kglw",
    "kg&lw",
    "kg and lw",
]

ARTIST_PREFIXES = [
    "king gizzard and the lizard wizard",
    "king gizzard & the lizard wizard",
    "king gizzard the lizard wizard",
    "king gizzard",
    "kglw",
]

# Parenthetical/bracketed groups containing any of these are upload noise, not
# part of the song title.
NOISE_WORDS = {
    "official", "video", "audio", "lyric", "lyrics", "visualizer", "visualiser",
    "full", "album", "stream", "live", "hd", "hq", "4k", "1080p", "remaster",
    "remastered", "music", "mv", "clip", "session", "performance", "cover",
    "reaction", "explained", "review", "trailer", "teaser", "snippet",
}

BRACKET_RE = re.compile(r"[\(\[\{]([^\)\]\}]*)[\)\]\}]")
FULL_ALBUM_RE = re.compile(r"\bfull\s+album\b", re.IGNORECASE)
LIVE_RE = re.compile(r"\blive\b|\bbootleg\b|\bconcert\b|\bat\s+the\b", re.IGNORECASE)


def normalize(text: str) -> str:
    """Fold a title to a comparable key: lowercase alphanumerics and spaces."""
    text = html.unescape(text or "").lower()
    text = text.replace("&", " and ")
    text = text.replace("’", "'").replace("‘", "'")
    text = re.sub(r"[^a-z0-9']+", " ", text)
    text = text.replace("'", "")
    return re.sub(r"\s+", " ", text).strip()


def strip_noise(title: str) -> str:
    """Remove upload-noise brackets and a leading artist credit."""
    def drop_if_noisy(match: re.Match) -> str:
        inner = normalize(match.group(1))
        if any(word in NOISE_WORDS for word in inner.split()):
            return " "
        return match.group(0)

    cleaned = BRACKET_RE.sub(drop_if_noisy, title)
    normalized = normalize(cleaned)

    for prefix in ARTIST_PREFIXES:
        prefix_norm = normalize(prefix)
        if normalized.startswith(prefix_norm):
            normalized = normalized[len(prefix_norm):].strip()
            break
    return normalized


def channel_names_band(channel: str | None) -> bool:
    name = normalize(channel or "")
    return any(p in name for p in ("king gizzard", "lizard wizard", "kglw"))


def is_band(record: dict, band_channels: set[str] | None = None) -> str | None:
    """Return the rule name that identifies this as KGLW, else None."""
    if channel_names_band(record.get("channel")):
        return "channel"

    title = normalize(record.get("title") or "")
    for pattern in BAND_TITLE_PATTERNS:
        if normalize(pattern) in title:
            return "title"

    # YouTube Music plays surface as bare track titles on auto-generated
    # "<something> - Topic" channels that never name the artist. Those channels
    # are per-release, so the channel id itself is the reliable signal.
    if band_channels and record.get("channel_id") in band_channels:
        return "channel-id"
    return None


def find_band_channels(
    records: list[dict],
    index: "AlbumIndex",
    min_matches: int = 2,
    min_ratio: float = 0.5,
) -> tuple[set[str], dict[str, tuple[int, int]]]:
    """Fingerprint auto-generated channels that host KGLW releases.

    A channel qualifies when enough of the *distinct* titles played from it are
    known KGLW tracks. Requiring a share of the channel's catalogue -- not just
    a raw hit count -- keeps big unrelated channels out when one of their song
    titles happens to collide with a KGLW track name.

    Returns (confident, borderline) where borderline maps channel_id to
    (matched, total) for titles that hit but fell under the thresholds.
    """
    from collections import defaultdict

    titles_by_channel: dict[str, set[str]] = defaultdict(set)
    named: set[str] = set()

    for record in records:
        channel_id = record.get("channel_id")
        if not channel_id:
            continue
        titles_by_channel[channel_id].add(strip_noise(record.get("title") or ""))
        if channel_names_band(record.get("channel")):
            named.add(channel_id)

    confident: set[str] = set(named)
    borderline: dict[str, tuple[int, int]] = {}

    for channel_id, titles in titles_by_channel.items():
        if channel_id in confident:
            continue
        matched = {t for t in titles if t in index.by_track}
        if not matched:
            continue
        ratio = len(matched) / len(titles)
        if len(matched) >= min_matches and ratio >= min_ratio:
            confident.add(channel_id)
        else:
            borderline[channel_id] = (len(matched), len(titles))

    return confident, borderline


def track_entries(album: dict):
    """Yield (title, length_ms) for an album, accepting either cache format.

    Older caches stored tracks as bare strings; newer ones store dicts with
    durations. Both are read so a half-upgraded cache never crashes a run.
    """
    for track in album.get("tracks") or []:
        if isinstance(track, str):
            yield track, None
        else:
            yield track.get("title"), track.get("length_ms")


def album_duration_ms(album: dict) -> int | None:
    """Total runtime, or None if any track's length is unknown."""
    lengths = [length for _, length in track_entries(album)]
    if not lengths or any(length is None for length in lengths):
        return None
    return sum(lengths)


class AlbumIndex:
    """Maps a normalized track title to its most likely album."""

    def __init__(self, data: dict):
        self.data = data
        self.albums = data["albums"]
        self.by_album_title: dict[str, dict] = {}
        self.by_track: dict[str, dict] = {}

        for album in sorted(self.albums, key=self._album_rank):
            # First writer wins, and albums are pre-sorted best-first.
            for album_key in self._title_aliases(album["title"]):
                self.by_album_title.setdefault(album_key, album)
            for title, length_ms in track_entries(album):
                if not title:
                    continue
                self.by_track.setdefault(
                    normalize(title),
                    {"album": album, "track": title, "length_ms": length_ms},
                )

        self._track_keys = list(self.by_track)

    @staticmethod
    def _title_aliases(title: str) -> list[str]:
        """Full title plus the short name people actually type.

        Nobody titles a video "PetroDragonic Apocalypse; or, Dawn of Eternal
        Night: An Annihilation of Planet Earth...", so the segment before the
        first ';' or ':' is indexed as an alias too. Very short aliases are
        dropped -- they collide with ordinary words.
        """
        keys = [normalize(title)]
        head = re.split(r"[;:]", title)[0]
        alias = normalize(head)
        if alias and alias != keys[0] and len(alias) >= 8:
            keys.append(alias)
        return keys

    @staticmethod
    def _album_rank(album: dict) -> tuple:
        """Studio albums first, then by release date -- the canonical home."""
        is_studio = album.get("primary_type") == "Album" and not album.get("secondary_types")
        is_ep = album.get("primary_type") == "EP"
        return (not is_studio, not is_ep, album.get("first_release_date") or "9999")

    def match_album_title(self, title: str) -> dict | None:
        """Find an album whose name appears in the video title."""
        key = normalize(title)
        best = None
        for album_key, album in self.by_album_title.items():
            # Require a word-boundary hit so "Polygondwanaland" does not match
            # inside an unrelated longer token.
            if album_key and re.search(rf"\b{re.escape(album_key)}\b", key):
                if best is None or len(album_key) > len(normalize(best["title"])):
                    best = album
        return best

    def find_tracks_in_title(self, title: str, min_chars: int = 8) -> list[dict]:
        """Find track names embedded in a longer title (live sets, medleys).

        Only called on rows already confirmed to be KGLW, so the risk is a
        track name colliding with ordinary words rather than another artist.
        Short names are skipped anyway -- "Dirt", "Bone", "Sense" and "Honey"
        are all real KGLW tracks and all far too common to match on.
        """
        key = normalize(title)
        found: list[tuple[str, dict]] = []
        for track_key, hit in self.by_track.items():
            if len(track_key) < min_chars:
                continue
            if re.search(rf"\b{re.escape(track_key)}\b", key):
                found.append((track_key, hit))

        # Drop names wholly contained in a longer match, so "Motor Spirit" does
        # not also count as part of a longer title containing it.
        found.sort(key=lambda pair: -len(pair[0]))
        kept: list[dict] = []
        claimed: list[str] = []
        for track_key, hit in found:
            if any(track_key in longer for longer in claimed):
                continue
            claimed.append(track_key)
            kept.append(hit)
        return kept

    def match_track(self, cleaned: str, fuzzy_cutoff: float = 0.90) -> tuple[dict | None, str]:
        """Exact then fuzzy track lookup. Returns (hit, how)."""
        if not cleaned:
            return None, "empty"
        hit = self.by_track.get(cleaned)
        if hit:
            return hit, "exact"

        close = difflib.get_close_matches(cleaned, self._track_keys, n=1, cutoff=fuzzy_cutoff)
        if close:
            return self.by_track[close[0]], "fuzzy"
        return None, "none"


def classify(
    records: Iterable[dict],
    index: AlbumIndex,
    band_channels: set[str] | None = None,
) -> list[dict]:
    """Annotate KGLW records with track/album attribution."""
    out = []
    for record in records:
        rule = is_band(record, band_channels)
        if not rule:
            continue

        title = record.get("title") or ""
        cleaned = strip_noise(title)
        entry = dict(record)
        entry["band_rule"] = rule
        entry["cleaned_title"] = cleaned
        entry["is_full_album"] = bool(FULL_ALBUM_RE.search(title))
        entry["is_live"] = bool(LIVE_RE.search(title))

        album_hit = index.match_album_title(title)
        track_hit, how = index.match_track(cleaned)

        # A "Full Album" upload is an album play, not a track play, even when
        # the album shares its name with a song on it (Nonagon Infinity does).
        if entry["is_full_album"] and album_hit:
            entry["album"] = album_hit["title"]
            entry["album_id"] = album_hit["id"]
            entry["track"] = None
            entry["match"] = "album-title"
        elif track_hit:
            entry["album"] = track_hit["album"]["title"]
            entry["album_id"] = track_hit["album"]["id"]
            entry["track"] = track_hit["track"]
            entry["match"] = how
        elif album_hit:
            entry["album"] = album_hit["title"]
            entry["album_id"] = album_hit["id"]
            entry["track"] = None
            entry["match"] = "album-title"
        else:
            entry["album"] = None
            entry["album_id"] = None
            entry["track"] = None
            entry["match"] = "unmatched"

        out.append(entry)
    return out


def load_index() -> AlbumIndex:
    return AlbumIndex(discography.load())
