# King Gizzard watch-history analysis

Works out which King Gizzard & the Lizard Wizard albums you've actually played,
from a Google Takeout YouTube history export.

Pure standard-library Python 3.9+. No dependencies, no install step.

## Quick start

```bash
# End to end, straight from the Takeout file
python3 -m kglw.analyze ~/Downloads/Takeout/YouTube\ and\ YouTube\ Music/history/watch-history.html

# Or in stages
python3 -m kglw.parse_history watch-history.html -o all.jsonl
python3 -m kglw.analyze all.jsonl --json report.json --dump kglw.jsonl
```

Refresh the cached discography (needs network; ~5 min at MusicBrainz's
1 req/sec limit):

```bash
python3 -m kglw.discography
python3 -m kglw.discography --stats
```

## How it works

**`parse_history.py`** — Takeout ships watch history as one enormous HTML file
with no newlines (67 MB / ~70k records in the case this was built against), so
it can't be read line-by-line and shouldn't go near a DOM parser. This reads it
in fixed-size chunks, splits on the record delimiter, and keeps memory flat
regardless of file size. Handles removed/private videos, YouTube Music rows,
HTML entities, and the narrow no-break space Google puts before AM/PM.

**`discography.py`** — Pulls the track→album mapping from MusicBrainz rather
than hard-coding it. The band has 265 release groups and 3,300+ tracks, and
hand-maintaining that is how you get wrong answers. Cached to
`data/discography.json` so analysis runs are reproducible and offline.

For each release group it picks the *standard* edition, not the longest one:
deluxe reissues carry bonus discs and instrumentals that would overstate album
length and skew per-track normalisation. The standard edition is the one
pressed most often, so its track count is the modal one.

**`match.py`** — Two separate problems, kept separate:

1. *Is this the band at all?* Decided by channel name, an explicit mention in
   the title, or channel-ID fingerprinting (below). Bare track titles on
   unrelated channels are **not** claimed — several KGLW songs ("The River",
   "Work This Time") are generic enough to collide with other artists.

2. *Which album is it?* Matched against the MusicBrainz tracklists. A track
   like "Big Fig Wasp" appears on 16 different releases; studio albums win over
   live records, bootlegs and demos, so it resolves to *Nonagon Infinity*.

The channel-ID fingerprinting matters more than it sounds. Roughly half of all
listening happens on YouTube Music, where rows look like this:

    Watched  Big Fig Wasp
    Release - Topic
    Aug 11, 2026, 12:26:32 PM MDT

Nothing there names the artist. But those auto-generated channels are
*per-release*, so the channel ID is a reliable fingerprint: if enough of the
distinct titles played from a channel are known KGLW tracks, the whole channel
counts. Requiring a *share* of the channel's catalogue rather than a raw hit
count keeps big unrelated channels out when one song title happens to collide —
without it, Fleetwood Mac and Daft Punk get pulled in.

## Reading the output

Two rankings, because "listened to most" is genuinely ambiguous:

- **Total plays** — raw count of play events. Biased toward long albums, since
  a 22-track record accumulates more events per listen than a 7-track one.
- **Estimated times played through** — track plays divided by album length,
  plus full-album uploads counted as one listen each. Length-neutral. Restricted
  to studio albums of 5+ tracks; dividing a few plays by a 2-track single
  produces meaningless numbers.

Watch history records *that* something was played, never *how much* of it, so a
30-second skip and a full listen are indistinguishable. Both metrics inherit
that limit.

The report ends with unattributed titles so coverage is auditable rather than
taken on trust.

## Known limitations

- Live concert footage, interviews, drum-cams and reaction videos are counted
  as KGLW plays but attributed to no album — correctly, since they aren't album
  listens. This is the bulk of what stays unmatched.
- Medleys and mashups ("Gaia/Motor Spirit Live at Red Rocks", "Murder of the
  Nonagon Fuzz") name several tracks at once and are left unattributed.
- Timezone abbreviations are mapped through a fixed table; an export from a
  zone outside that table keeps its local wall-clock time but gets no UTC
  instant.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

Covers entity decoding, timezone conversion, removed videos, records split
across read boundaries, studio-over-live album preference, album-vs-single name
collisions, and the false-positive rejection above.
