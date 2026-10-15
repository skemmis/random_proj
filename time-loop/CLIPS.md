# Clips for The Loop Hypothesis, piece 1

Each scene plays two video files: one from a film and one of Trump. Upload clips in the thread with a note saying which slot each one fills; Claude trims, compresses and publishes them. The page falls back to YouTube's four preview frames for any slot that has no file yet.

**Format.** Any common video format works; Claude converts it to MP4 (H.264). Clips of 5 to 30 seconds play best because each scene loops its clips. If you want a clip trimmed, give the start and end times. Each published file must be under 15 MB, so Claude encodes at about 720p.

**Sound.** In each split, the film clip plays first and the Trump clip second, so only one clip plays at a time. Sound is on: the page opens with one "Turn on sound" button.

| Slot | Scene | Suggested source |
|---|---|---|
| rules-film | 1. The rules don't apply | Groundhog Day, Phil drives down the railroad tracks. https://www.youtube.com/watch?v=50jZVcRgkno ("Groundhog Day \"I'm not going to live by their rules anymore.\"", David Q Heffner). Keep from Phil saying "I'm not going to live by their rules anymore" through the truck running along the tracks toward the train. |
| rules-trump | | DONE: NATO, May 25, 2017, Trump pushes past Duško Marković. MSNBC (Andrea Mitchell Reports) via the Internet Archive TV News Archive, panned by hand to stay on Trump, 576x720 |
| consequences-film | 2. No consequences | https://www.youtube.com/watch?v=ZHpXxAW3p_o ("Groundhog Day - \"What if there were no tomorrow?\"", Gale N Thrope). Keep from Phil asking the two men at the bowling-alley bar "What if there were no tomorrow?" through "That's the way I see it" (about 15 to 20 s). |
| consequences-trump | | DONE: Sioux Center, Iowa, Jan. 23, 2016, "Fifth Avenue". CNN (Smerconish) via the TV News Archive, 14.5 s, cropped tall |
| ennui-film | 3. Ennui | https://www.youtube.com/watch?v=vBeGQAvabOE ("Bill Murray - \"Groundhog Day\" winter prediction (HD)", Vlkoslak). Keep Phil's forecast at Gobbler's Knob, ending on "it's gonna last you for the rest of your life". |
| ennui-trump | | DONE: Oaks, Pa., Oct. 14, 2024, 24 s of Trump standing on stage while "Ave Maria" plays, about 7:45 pm. C-SPAN via the TV News Archive (CSPAN_20241014_200000_Public_Affairs_Events, item seconds 13505-13529), cropped tall |
| lines-film | 4. Same day, same lines | https://www.youtube.com/watch?v=XqSYC_vwhDg ("Groundhog Day (1993) - Ned Ryerson! Scene (1/8)", Movieclips). Keep from "Phil? Phil Connors?" through "Bing!" |
| lines-trump | | DONE: the sharks-and-electric-boats riff at four rallies, 56.5 s, each segment labelled with date and place: Anaheim Sept. 29, 2023; Ankeny Dec. 2, 2023; Las Vegas June 9, 2024; Grand Rapids July 20, 2024. All C-SPAN via the TV News Archive |
| butler-film | 5. Again. Again. Again. (inset) | Sam's pick (Oct 15): Edge of Tomorrow training sequence, https://www.youtube.com/watch?v=z1bVCdT5kso ("Edge of Tomorrow Extended Movie Clip - Training Sequence (2014)", Fandango at Home). Keep the stretch where Cage is shot, wakes and tries again, over and over; the whole run is fine, since the inset loops it under every relived July 13 and its RESET stamp. |
| butler-trump | 5. (full screen) | DONE: 20 seconds of the RSBN broadcast at 1280x720, first shot 10 seconds in |
| reaction-film | 6. Death holds no fear | https://www.youtube.com/watch?v=7FS56uRsnjo ("The First Time Andy Samberg & Christin Milioti Get Stuck In A Loop | Palm Springs", Prime Video UK & IE). Keep the arrow hitting Nyles and his calm reaction. |
| reaction-trump | | DONE: 13 seconds of the 1080p RSBN broadcast from about a minute after the shot, Trump rising and raising his fist, cropped tall by the reframe tool |

**Cropping.** Each split side is tall, so landscape clips are cropped to a 4:5 frame that follows the subject's face. `tools/reframe.py` does this automatically with OpenCV's face detector and smooths the virtual camera; manual centres can override it where the tracker loses the subject.

The scene layouts (side by side, or a draggable wipe) and all on-screen text are set in the CONTENT block at the top of `01-exhibits/template.html`.


Trump clips are pulled from the Internet Archive TV News Archive (archive.org/download/ID/ID.mp4?t=START/END, pieces under ~10 minutes), found with the GDELT TV API (api.gdeltproject.org/api/v2/tv/tv, mode=clipgallery). All six Trump slots are filled; the six film slots wait on Sam.

Film links checked October 15, 2026, against YouTube's own title and uploader for each video (its oEmbed service). YouTube was refusing page loads from this environment that day, so the clip lengths and descriptions were not read and the keep points are cues from the dialogue, not timestamps.

## The teaser (00-teaser/, added October 15, 2026)

The teaser before the opening uses Trump footage already in hand (the RSBN Butler broadcast and the five tall Trump clips) and, for the films, YouTube still frames until Sam's clips arrive. Two more film clips would replace stills there:

| Slot | Scene | Suggested source |
|---|---|---|
| alarm-film | Teaser, each morning | Groundhog Day: the clock radio flips from 5:59 to 6:00 and "I Got You Babe" starts. Movieclips upload: https://www.youtube.com/watch?v=hQCG2AwzTxA ("Groundhog Day" scene, title confirmed by YouTube's oEmbed). Keep the flip and the first bars of the song, about 5 s. |
| wake-film | Teaser, each morning | Edge of Tomorrow: Cage jolts awake on the tarmac at Heathrow, "On your feet, maggot!" It appears in the training clip already on the list (https://www.youtube.com/watch?v=z1bVCdT5kso); keep two or three of the wake-ups, about 1 s each. |

Until then the page draws its own clock radio and uses YouTube stills for Phil, Cage and Ned.
