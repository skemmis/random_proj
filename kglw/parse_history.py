"""Stream-parse a Google Takeout ``watch-history.html`` into JSONL.

Takeout ships watch history as a single enormous HTML file (often 50-500 MB)
with no newlines, so it cannot be read line-by-line and should not be loaded
into a DOM parser. This module reads the file in fixed-size chunks and splits
on the record delimiter, keeping memory flat regardless of file size.

Stdlib only: no bs4/lxml, so it runs on a stock python3 anywhere.

Usage:
    python3 -m kglw.parse_history watch-history.html -o watches.jsonl
    python3 -m kglw.parse_history watch-history.html -o kglw.jsonl --grep "king gizzard"
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from typing import Iterator, TextIO

# Each history entry is wrapped in a div with this class prefix.
RECORD_MARKER = '<div class="outer-cell'

# The first body-1 content cell holds the action, links and timestamp. A second
# body-1 cell (text-right) is usually empty, and a caption cell holds the
# "Why is this here?" boilerplate -- both are ignored.
CONTENT_CELL_RE = re.compile(
    r'<div class="content-cell[^"]*mdl-typography--body-1(?![^"]*text-right)[^"]*"[^>]*>(.*?)</div>',
    re.DOTALL,
)
HEADER_CELL_RE = re.compile(
    r'<div class="header-cell.*?<p[^>]*>(.*?)</p>', re.DOTALL
)
ANCHOR_RE = re.compile(r'<a\s+[^>]*href="([^"]*)"[^>]*>(.*?)</a>', re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")

VIDEO_ID_RE = re.compile(r"(?:watch\?v=|youtu\.be/|/shorts/)([A-Za-z0-9_-]{11})")
CHANNEL_ID_RE = re.compile(r"/channel/([A-Za-z0-9_-]+)")

# "Aug 11, 2026, 7:52:46 PM PDT" -- the trailing token is a timezone
# abbreviation that strptime cannot consume portably, so it is split off first.
TIMESTAMP_RE = re.compile(
    r"([A-Z][a-z]{2}\s+\d{1,2},\s+\d{4},\s+\d{1,2}:\d{2}:\d{2}\s*[AP]M)\s*([A-Z]{2,5})?\s*$"
)

# Offsets for the abbreviations Takeout actually emits. Used only to derive a
# comparable UTC instant; the original local wall-clock time is kept verbatim.
TZ_OFFSETS = {
    "UTC": 0, "GMT": 0, "BST": 1, "IST": 1, "WET": 0, "WEST": 1,
    "CET": 1, "CEST": 2, "EET": 2, "EEST": 3,
    "EST": -5, "EDT": -4, "CST": -6, "CDT": -5,
    "MST": -7, "MDT": -6, "PST": -8, "PDT": -7,
    "AKST": -9, "AKDT": -8, "HST": -10,
    "AEST": 10, "AEDT": 11, "ACST": 9.5, "ACDT": 10.5,
    "AWST": 8, "NZST": 12, "NZDT": 13, "JST": 9, "KST": 9,
}


def iter_records(fh: TextIO, chunk_size: int = 1 << 20) -> Iterator[str]:
    """Yield each entry's raw HTML without holding the whole file in memory."""
    buf = ""
    seen_first = False
    while True:
        chunk = fh.read(chunk_size)
        if not chunk:
            break
        buf += chunk
        parts = buf.split(RECORD_MARKER)
        # The trailing part may be a partial record; carry it to the next read.
        buf = parts.pop()
        for part in parts:
            if not seen_first:
                # Text before the first marker is the document preamble.
                seen_first = True
                continue
            yield part
    if seen_first and buf.strip():
        yield buf


def _clean(fragment: str) -> str:
    """Strip tags and entities, and normalise Unicode spaces to plain spaces."""
    text = TAG_RE.sub(" ", fragment)
    text = html.unescape(text)
    # NBSP, narrow NBSP (used before AM/PM), thin space, zero-width space.
    text = text.replace(" ", " ").replace(" ", " ")
    text = text.replace(" ", " ").replace("​", "")
    return re.sub(r"\s+", " ", text).strip()


def _to_utc(local: datetime, tz: str | None) -> str | None:
    if tz is None or tz not in TZ_OFFSETS:
        return None
    offset = timedelta(hours=TZ_OFFSETS[tz])
    return local.replace(tzinfo=timezone(offset)).astimezone(timezone.utc).isoformat()


def parse_record(raw: str) -> dict | None:
    """Turn one entry's HTML into a dict, or None if it holds no usable data."""
    content_match = CONTENT_CELL_RE.search(raw)
    if not content_match:
        return None
    content = content_match.group(1)

    header_match = HEADER_CELL_RE.search(raw)
    product = _clean(header_match.group(1)) if header_match else ""

    video_id = title = channel = channel_id = None
    for href, label in ANCHOR_RE.findall(content):
        href = html.unescape(href)
        label_text = _clean(label)
        vid = VIDEO_ID_RE.search(href)
        if vid and video_id is None:
            video_id, title = vid.group(1), label_text
            continue
        if ("/channel/" in href or "/@" in href or "/user/" in href) and channel is None:
            channel = label_text
            cid = CHANNEL_ID_RE.search(href)
            channel_id = cid.group(1) if cid else None

    flat = _clean(content)

    # Leading verb: "Watched", "Searched for", "Visited". Removed or private
    # videos appear as "Watched a video that has been removed" with no anchor.
    action_match = re.match(r"^(Watched|Searched for|Visited|Viewed)\b", flat)
    action = action_match.group(1) if action_match else None

    if title is None and action:
        # No anchor -- keep whatever text followed the verb, minus the date.
        remainder = flat[len(action):].strip()
        remainder = TIMESTAMP_RE.sub("", remainder).strip(" ,")
        title = remainder or None

    ts_match = TIMESTAMP_RE.search(flat)
    local_iso = tz = utc_iso = None
    if ts_match:
        stamp, tz = ts_match.group(1), ts_match.group(2)
        stamp = re.sub(r"\s+", " ", stamp).strip()
        try:
            local = datetime.strptime(stamp, "%b %d, %Y, %I:%M:%S %p")
            local_iso = local.isoformat()
            utc_iso = _to_utc(local, tz)
        except ValueError:
            local_iso = stamp

    if title is None and local_iso is None:
        return None

    return {
        "product": product,
        "action": action,
        "video_id": video_id,
        "title": title,
        "channel": channel,
        "channel_id": channel_id,
        "watched_at_local": local_iso,
        "tz": tz,
        "watched_at_utc": utc_iso,
    }


def parse_file(path: str, grep: str | None = None) -> Iterator[dict]:
    """Yield parsed records, optionally keeping only those matching `grep`."""
    needle = grep.lower() if grep else None
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for raw in iter_records(fh):
            record = parse_record(raw)
            if record is None:
                continue
            if needle:
                haystack = f"{record.get('title') or ''} {record.get('channel') or ''}".lower()
                if needle not in haystack:
                    continue
            yield record


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("input", help="path to watch-history.html")
    ap.add_argument("-o", "--output", help="JSONL output path (default: stdout)")
    ap.add_argument("--grep", help="only keep records whose title/channel contain this")
    ap.add_argument("--limit", type=int, help="stop after N matching records")
    args = ap.parse_args(argv)

    out = open(args.output, "w", encoding="utf-8") if args.output else sys.stdout
    total = 0
    try:
        for record in parse_file(args.input, grep=args.grep):
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            total += 1
            if args.limit and total >= args.limit:
                break
    finally:
        if args.output:
            out.close()

    print(f"wrote {total:,} records", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
