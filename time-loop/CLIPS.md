# Clips for The Loop Hypothesis, piece 1

Each scene plays two video files: one from a film and one of Trump. Upload clips in the thread with a note saying which slot each one fills; Claude trims, compresses and publishes them. The page falls back to YouTube's four preview frames for any slot that has no file yet.

**Format.** Any common video format works; Claude converts it to MP4 (H.264). Clips of 5 to 30 seconds play best because each scene loops its clips. If you want a clip trimmed, give the start and end times. Each published file must be under 15 MB, so Claude encodes at about 720p.

**Sound.** In each split, the film clip plays first and the Trump clip second, so only one clip plays at a time. Sound is off until the viewer presses Sound in the corner.

| Slot | Scene | Suggested source |
|---|---|---|
| rules-film | 1. The rules don't apply | Groundhog Day, Phil drives down the railroad tracks |
| rules-trump | | DONE: NATO, May 25, 2017, Trump pushes past Duško Marković. MSNBC (Andrea Mitchell Reports) via the Internet Archive TV News Archive, panned by hand to stay on Trump, 576x720 |
| consequences-film | 2. No consequences | Groundhog Day, "What if there were no tomorrow?" at the bowling alley |
| consequences-trump | | DONE: Sioux Center, Iowa, Jan. 23, 2016, "Fifth Avenue". CNN (Smerconish) via the TV News Archive, 14.5 s, cropped tall |
| ennui-film | 3. Ennui | Groundhog Day, the "rest of your life" forecast |
| ennui-trump | | DONE: Oaks, Pa., Oct. 14, 2024, 24 s of Trump standing on stage while "Ave Maria" plays, about 7:45 pm. C-SPAN via the TV News Archive (CSPAN_20241014_200000_Public_Affairs_Events, item seconds 13505-13529), cropped tall |
| lines-film | 4. Same day, same lines | Groundhog Day, Ned Ryerson greets Phil (Movieclips: youtube.com/watch?v=XqSYC_vwhDg); several mornings cut together if you can |
| lines-trump | | DONE: the sharks-and-electric-boats riff at four rallies, 56.5 s, each segment labelled with date and place: Anaheim Sept. 29, 2023; Ankeny Dec. 2, 2023; Las Vegas June 9, 2024; Grand Rapids July 20, 2024. All C-SPAN via the TV News Archive |
| butler-film | 5. Again. Again. Again. (inset) | Edge of Tomorrow, Cage dying on the beach and waking again |
| butler-trump | 5. (full screen) | DONE: 20 seconds of the RSBN broadcast at 1280x720, first shot 10 seconds in |
| reaction-film | 6. Death holds no fear | Palm Springs, Roy shoots Nyles with an arrow and Nyles shrugs it off |
| reaction-trump | | DONE: 13 seconds of the 1080p RSBN broadcast from about a minute after the shot, Trump rising and raising his fist, cropped tall by the reframe tool |

**Cropping.** Each split side is tall, so landscape clips are cropped to a 4:5 frame that follows the subject's face. `tools/reframe.py` does this automatically with OpenCV's face detector and smooths the virtual camera; manual centres can override it where the tracker loses the subject.

The scene layouts (side by side, or a draggable wipe) and all on-screen text are set in the CONTENT block at the top of `01-exhibits/template.html`.


Trump clips are pulled from the Internet Archive TV News Archive (archive.org/download/ID/ID.mp4?t=START/END, pieces under ~10 minutes), found with the GDELT TV API (api.gdeltproject.org/api/v2/tv/tv, mode=clipgallery). All six Trump slots are filled; the six film slots wait on Sam.