# Clips for The Loop Hypothesis, piece 1

Each scene plays two video files: one from a film and one of Trump. Upload clips in the thread with a note saying which slot each one fills; Claude trims, compresses and publishes them. The page falls back to YouTube's four preview frames for any slot that has no file yet.

**Format.** Any common video format works; Claude converts it to MP4 (H.264). Clips of 5 to 30 seconds play best because each scene loops its clips. If you want a clip trimmed, give the start and end times. Each published file must be under 15 MB, so Claude encodes at about 720p.

**Sound.** In each split, the film clip plays first and the Trump clip second, so only one clip plays at a time. Sound is on: the page opens with one "Turn on sound" button.

| Slot | Scene | Suggested source |
|---|---|---|
| rules-film | 1. The rules don't apply | DONE (Oct 15, with sound; trimmed per Sam) from Sam's "no consequences" upload and its audio: 1:47-1:59, the train's headlights, the swerve off the tracks, then Phil grinning: "I'm not going to live by their rules anymore." |
| rules-trump | | DONE: NATO, May 25, 2017, Trump pushes past Duško Marković. MSNBC (Andrea Mitchell Reports) via the Internet Archive TV News Archive, panned by hand to stay on Trump, 576x720 |
| consequences-film | 2. No consequences | DONE (Oct 15, with sound): 0:05.5-0:25.5 of the same upload, Phil in the car: "What if there were no tomorrow?" ... "That would mean there would be no consequences." |
| consequences-trump | | DONE: Sioux Center, Iowa, Jan. 23, 2016, "Fifth Avenue". CNN (Smerconish) via the TV News Archive, 14.5 s, cropped tall |
| ennui-film | 3. Ennui | DONE (Oct 15, with sound) from Sam's "winter prediction" upload: 0:00-0:16.8, the whole forecast ending "...the rest of your life." |
| ennui-trump | | DONE: Oaks, Pa., Oct. 14, 2024, 24 s of Trump standing on stage while "Ave Maria" plays, about 7:45 pm. C-SPAN via the TV News Archive (CSPAN_20241014_200000_Public_Affairs_Events, item seconds 13505-13529), cropped tall |
| lines-film | 4. Same day, same lines | DONE (Oct 15, SILENT) from Sam's "ned" upload: 0:14-0:40, Ned greets Phil. Sam's audio set had no track for this one; send ned audio to add sound. |
| lines-trump | | DONE: the sharks-and-electric-boats riff at four rallies, 56.5 s, each segment labelled with date and place: Anaheim Sept. 29, 2023; Ankeny Dec. 2, 2023; Las Vegas June 9, 2024; Grand Rapids July 20, 2024. All C-SPAN via the TV News Archive |
| butler-film | 5. Again. Again. Again. (split, film side) | DONE (Oct 15) from Sam's "training" upload and audio: 1:54-2:12, 2:52.5-2:58.5 (Rita shoots him; he wakes on the tarmac) and 3:36-3:48, 36 s, letterbox cropped, tall 4:5 (face tracker, 2.5 s smoothing). |
| butler-trump | 5. (split, Trump side) | DONE: 20 seconds of the broadcast, caption bar cropped, tall 4:5 held on Trump, first shot 10 seconds in. (Sam dropped the loop simulator, Oct 15.) |
| reaction-film | 6. Death holds no fear | DONE (Oct 15, with sound) from Sam's "the arrow" upload: 0:43.2-0:44.4 (the arrow hits Nyles) then 0:02-0:10 (Nyles lounging on his pool float). |
| reaction-trump | | DONE: 13 seconds of the 1080p broadcast from about a minute after the shot, Trump rising and raising his fist, cropped tall by the reframe tool |

**Cropping.** Each split side is tall, so landscape clips are cropped to a 4:5 frame that follows the subject's face. `tools/reframe.py` does this automatically with OpenCV's face detector and smooths the virtual camera; manual centres can override it where the tracker loses the subject.

The scene layouts (side by side, or a draggable wipe) and all on-screen text are set in the CONTENT block at the top of `01-exhibits/template.html`.


Trump clips are pulled from the Internet Archive TV News Archive (archive.org/download/ID/ID.mp4?t=START/END, pieces under ~10 minutes), found with the GDELT TV API (api.gdeltproject.org/api/v2/tv/tv, mode=clipgallery). All six Trump slots are filled; the six film slots wait on Sam.

Film links checked October 15, 2026, against YouTube's own title and uploader for each video (its oEmbed service). YouTube was refusing page loads from this environment that day, so the clip lengths and descriptions were not read and the keep points are cues from the dialogue, not timestamps.

## The teaser (00-teaser/, added October 15, 2026)

The teaser before the opening uses Trump footage already in hand (the Butler broadcast and the five tall Trump clips) and, for the films, YouTube still frames until Sam's clips arrive. Two more film clips would replace stills there:

| Slot | Scene | Suggested source |
|---|---|---|
| alarm-film | Teaser, each morning | Groundhog Day: the clock radio flips from 5:59 to 6:00 and "I Got You Babe" starts. Movieclips upload: https://www.youtube.com/watch?v=hQCG2AwzTxA ("Groundhog Day" scene, title confirmed by YouTube's oEmbed). Keep the flip and the first bars of the song, about 5 s. |
| wake-film | Teaser, each morning | Edge of Tomorrow: Cage jolts awake on the tarmac at Heathrow, "On your feet, maggot!" It appears in the training clip already on the list (https://www.youtube.com/watch?v=z1bVCdT5kso); keep two or three of the wake-ups, about 1 s each. |

Until then the page draws its own clock radio and uses YouTube stills for Phil, Cage and Ned.


Oct 15: every film slot is filled. Sam's uploads and his separate audio tracks are kept in time-loop/sources/; the audio files run the same length as their videos, so they were laid in from the same start time. The teaser now uses real footage too: the film's own 6:00 clock radio (a still from the end of the "winter prediction" upload), the forecast, Cage waking after the beach explosion ("wake up" 1:27.8-1:31.6), Cage waking on the tarmac ("training" 2:55.6-2:58.2), the train and Ned.

## New finds: Trump coming to (Oct 15, for the teaser)

All from C-SPAN on the Internet Archive TV News Archive, at 640x480 (the archive's best). Clip URL: archive.org/download/ID/ID.mp4?t=START/END, at most 300 s per request. Copies in sources/daze/; previews in the clip cutter.

| File | What | Item and seconds |
|---|---|---|
| cabinet-nod.mp4 | Eyes shut, chin on chest; head jerks up about 1:33 in; opens his eyes and ends the meeting about 2:12 | CSPAN3_20251202_164900_President_Trump_Holds_a_Cabinet_Meeting, 6820-6960 |
| coal-nod.mp4 | Eyes closed while Burgum speaks; deeper nod, head snaps up about 0:47 | CSPAN_20260604_192200_POTUS_President_Trump_Makes_Announcement_on_Clean_Coal, 1195-1255 |
| didnt-sleep.mp4 | "I didn't sleep, I just closed them because I wanted to get the hell out of here" | CSPAN_20260129_163900_POTUS_Pres._Trump_Holds_Cabinet_Meeting, 1510-1560 |
| never-seen.mp4 | "There's never been anything like this," about four times in 30 s (from captions; not checked on screen) | CSPAN_20251106_170200_President_Trump_on_Lowering_Price_of_Weight_Loss_Drugs, 655-700 |

Also found, not cut: the "Hannibal Lecter" riff at three rallies (Chesapeake, Va., June 28, 2024, ~1502 s; St. Cloud, Minn., July 27, 2024, ~1151 s; Flint, Mich., Sept. 17, 2024, ~1792 s), for "same lines".
