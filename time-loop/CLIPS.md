# Clips for The Loop Hypothesis, piece 1

Each scene plays two video files: one from a film and one of Trump. Upload clips in the thread with a note saying which slot each one fills; Claude trims, compresses and publishes them. The page falls back to YouTube's four preview frames for any slot that has no file yet.

**Format.** Any common video format works; Claude converts it to MP4 (H.264). Clips of 5 to 30 seconds play best because each scene loops its clips. If you want a clip trimmed, give the start and end times. Each published file must be under 15 MB, so Claude encodes at about 720p.

**Sound.** In each split, the film clip plays first and the Trump clip second, so only one clip plays at a time. Sound is off until the viewer presses Sound in the corner.

| Slot | Scene | Suggested source |
|---|---|---|
| rules-film | 1. The rules don't apply | Groundhog Day, Phil drives down the railroad tracks |
| rules-trump | | NATO, May 25, 2017, Trump pushes past Duško Marković (AP: youtube.com/watch?v=Iimj0j4NYME) |
| consequences-film | 2. No consequences | Groundhog Day, "What if there were no tomorrow?" at the bowling alley |
| consequences-trump | | Sioux Center, Iowa, Jan. 23, 2016, "Fifth Avenue" (CNN: youtube.com/watch?v=iTACH1eVIaA) |
| recall-film | 3. Perfect recall (under review) | Groundhog Day, "I'm a god" in the diner |
| recall-trump | | Fox News, July 22, 2020, "Person, woman, man, camera, TV" |
| ennui-film | 4. Ennui | Groundhog Day, the "rest of your life" forecast |
| ennui-trump | | Oaks, Pa., Oct. 14, 2024, swaying to music |
| lines-film | 5. Same day, same lines | Groundhog Day, Ned Ryerson greets Phil (Movieclips: youtube.com/watch?v=XqSYC_vwhDg); several mornings cut together if you can |
| lines-trump | | Several rallies where Trump tells the same sharks-and-electric-boats riff, cut together. Candidates: Las Vegas, June 9, 2024 (youtube.com/watch?v=bqbmTnr9NSE); a bill signing (Palm Beach Post: youtube.com/watch?v=Hix5xk9ZH24); a 2026 event (USA Today: youtube.com/watch?v=TOb0dhLFBhs); an earlier version (Guardian: youtube.com/watch?v=XhgzcZH3SQ4). Send the separate clips and Claude splices them. |
| butler-film | 6. Again. Again. Again. (inset) | Edge of Tomorrow, Cage dying on the beach and waking again |
| butler-trump | 6. (full screen) | DONE: 20 seconds of the RSBN broadcast, first shot 10 seconds in |
| reaction-film | 7. Death holds no fear | Palm Springs, Roy shoots Nyles with an arrow and Nyles shrugs it off |
| reaction-trump | | DONE: 13 seconds of the RSBN broadcast from about a minute after the shot, Trump rising and raising his fist, cropped tall by the reframe tool |

**Cropping.** Each split side is tall, so landscape clips are cropped to a 4:5 frame that follows the subject's face. `tools/reframe.py` does this automatically with OpenCV's face detector and smooths the virtual camera; manual centres can override it where the tracker loses the subject.

The scene layouts (side by side, or a draggable wipe) and all on-screen text are set in the CONTENT block at the top of `01-exhibits/template.html`.
