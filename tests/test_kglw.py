"""Tests for the parser and matcher. Stdlib unittest -- no pytest needed.

    python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kglw import match, parse_history  # noqa: E402

FIXTURE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "sample-watch-history.html")

# A miniature discography exercising the cases that actually caused bugs:
# a track that lives on both a studio album and a live record, and an album
# sharing its name with a single.
FAKE_DISCOGRAPHY = {
    "albums": [
        {
            "id": "studio-nonagon",
            "title": "Nonagon Infinity",
            "first_release_date": "2016-04-29",
            "primary_type": "Album",
            "secondary_types": [],
            "tracks": ["Robot Stop", "Big Fig Wasp", "Gamma Knife"],
        },
        {
            "id": "live-nonagon",
            "title": "Nonagon Infinity Live",
            "first_release_date": "2024-01-01",
            "primary_type": "Album",
            "secondary_types": ["Live", "Compilation"],
            "tracks": ["Robot Stop", "Big Fig Wasp"],
        },
        {
            "id": "studio-quarters",
            "title": "Quarters!",
            "first_release_date": "2015-05-01",
            "primary_type": "Album",
            "secondary_types": [],
            "tracks": ["The River", "Infinite Rise"],
        },
        {
            "id": "single-river",
            "title": "The River",
            "first_release_date": "2015-06-01",
            "primary_type": "Single",
            "secondary_types": [],
            "tracks": ["The River"],
        },
        {
            "id": "studio-petro",
            "title": "PetroDragonic Apocalypse; or, Dawn of Eternal Night",
            "first_release_date": "2023-06-16",
            "primary_type": "Album",
            "secondary_types": [],
            "tracks": ["Motor Spirit", "Gila Monster"],
        },
    ]
}


class TestParser(unittest.TestCase):
    def setUp(self):
        self.records = list(parse_history.parse_file(FIXTURE))

    def test_finds_every_record(self):
        self.assertEqual(len(self.records), 6)

    def test_extracts_fields(self):
        first = self.records[0]
        self.assertEqual(first["title"], "Rattlesnake")
        self.assertEqual(first["video_id"], "aaaaaaaaaaa")
        self.assertEqual(first["channel"], "King Gizzard & The Lizard Wizard")
        self.assertEqual(first["product"], "YouTube")

    def test_decodes_entities(self):
        titles = [r["title"] for r in self.records]
        self.assertIn("Bob's Burgers Best Moments", titles)
        self.assertTrue(any("&" in t for t in titles if t))

    def test_timestamp_and_timezone(self):
        first = self.records[0]
        self.assertEqual(first["watched_at_local"], "2026-08-11T19:52:46")
        self.assertEqual(first["tz"], "PDT")
        # PDT is UTC-7, so the instant rolls into the next day.
        self.assertEqual(first["watched_at_utc"], "2026-08-12T02:52:46+00:00")

    def test_removed_video_still_yields_a_row(self):
        removed = [r for r in self.records if r["video_id"] is None and r["action"] == "Watched"]
        self.assertTrue(removed)
        self.assertIsNotNone(removed[0]["watched_at_local"])

    def test_chunk_boundaries_do_not_split_records(self):
        """Records must survive being cut across read boundaries."""
        with open(FIXTURE, encoding="utf-8") as fh:
            tiny = [parse_history.parse_record(r) for r in parse_history.iter_records(fh, chunk_size=64)]
        tiny = [r for r in tiny if r]
        self.assertEqual(len(tiny), len(self.records))
        self.assertEqual([r["title"] for r in tiny], [r["title"] for r in self.records])


class TestNormalisation(unittest.TestCase):
    def test_normalize_folds_punctuation_and_case(self):
        self.assertEqual(match.normalize("I'm In Your Mind Fuzz"), "im in your mind fuzz")
        self.assertEqual(match.normalize("K.G."), "k g")

    def test_strips_artist_prefix_and_upload_noise(self):
        self.assertEqual(
            match.strip_noise("King Gizzard & The Lizard Wizard - Rattlesnake (Official Video)"),
            "rattlesnake",
        )

    def test_keeps_meaningful_parentheses(self):
        # "(Interlude)" carries no noise word, so it must survive.
        self.assertIn("interlude", match.strip_noise("Some Song (Interlude)"))


class TestAlbumIndex(unittest.TestCase):
    def setUp(self):
        self.index = match.AlbumIndex(FAKE_DISCOGRAPHY)

    def test_prefers_studio_album_over_live_release(self):
        hit, how = self.index.match_track("big fig wasp")
        self.assertEqual(how, "exact")
        self.assertEqual(hit["album"]["title"], "Nonagon Infinity")

    def test_prefers_album_over_same_named_single(self):
        hit, _ = self.index.match_track("the river")
        self.assertEqual(hit["album"]["title"], "Quarters!")

    def test_long_subtitled_album_matches_its_short_name(self):
        album = self.index.match_album_title(
            "PetroDragonic Apocalypse (Live '24) Full Album Concert"
        )
        self.assertIsNotNone(album)
        self.assertEqual(album["id"], "studio-petro")

    def test_short_alias_does_not_match_unrelated_text(self):
        self.assertIsNone(self.index.match_album_title("a totally unrelated video title"))


class TestClassification(unittest.TestCase):
    def setUp(self):
        self.index = match.AlbumIndex(FAKE_DISCOGRAPHY)

    def test_full_album_upload_counts_as_album_not_track(self):
        record = {
            "title": "King Gizzard & The Lizard Wizard - Nonagon Infinity (Full Album)",
            "channel": "Flightless Records",
        }
        entry = match.classify([record], self.index)[0]
        self.assertTrue(entry["is_full_album"])
        self.assertEqual(entry["album"], "Nonagon Infinity")
        self.assertIsNone(entry["track"])

    def test_bare_title_on_unrelated_channel_is_not_claimed(self):
        """'The River' is a KGLW song, but this is plainly not KGLW."""
        record = {"title": "The River", "channel": "Bruce Springsteen - Topic", "channel_id": "UCother"}
        self.assertEqual(match.classify([record], self.index), [])

    def test_topic_channel_is_identified_by_channel_id(self):
        records = [
            {"title": "Robot Stop", "channel": "Release - Topic", "channel_id": "UCkglw"},
            {"title": "Gamma Knife", "channel": "Release - Topic", "channel_id": "UCkglw"},
        ]
        confident, _ = match.find_band_channels(records, self.index)
        self.assertIn("UCkglw", confident)
        entries = match.classify(records, self.index, confident)
        self.assertEqual(len(entries), 2)
        self.assertEqual({e["album"] for e in entries}, {"Nonagon Infinity"})

    def test_unrelated_channel_with_one_collision_is_rejected(self):
        records = [{"title": "The River", "channel": "Other - Topic", "channel_id": "UCx"}]
        records += [
            {"title": f"Unrelated Song {i}", "channel": "Other - Topic", "channel_id": "UCx"}
            for i in range(10)
        ]
        confident, borderline = match.find_band_channels(records, self.index)
        self.assertNotIn("UCx", confident)
        self.assertIn("UCx", borderline)


FAKE_TIMED = {
    "albums": [
        {
            "id": "studio-nonagon",
            "title": "Nonagon Infinity",
            "first_release_date": "2016-04-29",
            "primary_type": "Album",
            "secondary_types": [],
            "tracks": [
                {"title": "Robot Stop", "length_ms": 200_000},
                {"title": "Big Fig Wasp", "length_ms": 160_000},
                {"title": "Evil Death Roll", "length_ms": 400_000},
            ],
        },
        {
            "id": "studio-petro",
            "title": "PetroDragonic Apocalypse",
            "first_release_date": "2023-06-16",
            "primary_type": "Album",
            "secondary_types": [],
            "tracks": [
                {"title": "Motor Spirit", "length_ms": 300_000},
                {"title": "Gila Monster", "length_ms": 360_000},
            ],
        },
    ]
}


class TestTrackFormats(unittest.TestCase):
    def test_reads_legacy_string_tracks(self):
        album = {"tracks": ["A", "B"]}
        self.assertEqual(list(match.track_entries(album)), [("A", None), ("B", None)])

    def test_reads_timed_tracks(self):
        album = FAKE_TIMED["albums"][1]
        self.assertEqual(match.album_duration_ms(album), 660_000)

    def test_duration_is_none_when_a_track_length_is_missing(self):
        album = {"tracks": [{"title": "A", "length_ms": 1000}, {"title": "B", "length_ms": None}]}
        self.assertIsNone(match.album_duration_ms(album))


class TestMinutes(unittest.TestCase):
    def setUp(self):
        from kglw import minutes

        self.minutes = minutes
        self.index = match.AlbumIndex(FAKE_TIMED)

    def test_single_track_play_uses_track_duration(self):
        entry = {"track": "Robot Stop", "album": "Nonagon Infinity", "album_id": "studio-nonagon"}
        segments, source = self.minutes.segments_for(entry, self.index)
        self.assertEqual(source, "track")
        self.assertEqual(sum(s["length_ms"] for s in segments), 200_000)

    def test_full_album_play_uses_whole_record(self):
        entry = {"is_full_album": True, "album_id": "studio-nonagon", "album": "Nonagon Infinity"}
        segments, source = self.minutes.segments_for(entry, self.index)
        self.assertEqual(source, "album")
        self.assertEqual(sum(s["length_ms"] for s in segments), 760_000)

    def test_live_medley_recovers_each_named_track(self):
        entry = {"title": "Gila Monster/Motor Spirit Live at Red Rocks 6/7/23"}
        segments, source = self.minutes.segments_for(entry, self.index)
        self.assertEqual(source, "title-scan")
        self.assertEqual({s["track"] for s in segments}, {"Gila Monster", "Motor Spirit"})
        self.assertEqual(sum(s["length_ms"] for s in segments), 660_000)

    def test_interviews_contribute_no_time(self):
        for title in (
            "Talking to King Gizzard & The Lizard Wizard (Stu)",
            "Old Composer Reacts to King Gizzard",
            "King Gizzard on the Midnight Chats podcast",
            "How To Get Into King Gizzard & The Lizard Wizard",
        ):
            self.assertTrue(self.minutes.is_non_music(title), title)
            segments, source = self.minutes.segments_for({"title": title}, self.index)
            self.assertEqual(segments, [])
            self.assertEqual(source, "none")

    def test_interview_naming_a_track_still_contributes_nothing(self):
        """Talk must not bank a track's runtime just by mentioning it."""
        entry = {"title": "Motor Spirit explained - a track by track review"}
        segments, _ = self.minutes.segments_for(entry, self.index)
        self.assertEqual(segments, [])

    def test_short_track_names_are_not_scanned_from_prose(self):
        # A hypothetical 'Dirt'-length name must not match inside prose.
        hits = self.index.find_tracks_in_title("some video about a robot stopping")
        self.assertEqual(hits, [])

    def test_monthly_series_fills_gaps(self):
        entries = [
            {"track": "Robot Stop", "album": "Nonagon Infinity", "album_id": "studio-nonagon",
             "watched_at_utc": "2024-01-05T00:00:00+00:00"},
            {"track": "Robot Stop", "album": "Nonagon Infinity", "album_id": "studio-nonagon",
             "watched_at_utc": "2024-04-05T00:00:00+00:00"},
        ]
        report = self.minutes.summarise(entries, self.index)
        self.assertEqual(report["months"], ["2024-01", "2024-02", "2024-03", "2024-04"])
        self.assertEqual(report["minutes_by_month"]["2024-02"], 0)
        self.assertAlmostEqual(report["total_minutes"], 6.7, places=1)


if __name__ == "__main__":
    unittest.main()
