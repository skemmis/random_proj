# The Loop Hypothesis

Sam started this spin-off of the Butler project on October 13, 2026. It is a straight-faced, half-satirical investigation of the claim that Donald Trump is trapped in a time loop like the one in *Groundhog Day*, told as a series of New York Times-style interactive pages, one idea per page. The "Time loop" thread owns this folder. The plan, with every film, trait and clip, is in `PLAN.md`.

| Piece | Folder | Published page |
|---|---|---|
| 1. Is Donald Trump Living the Same Day Over and Over? Seven traits of time-loop heroes set beside Trump's record, ending with the Butler shooting and a loop simulator built on the 1-in-625 figure | `01-exhibits/` | https://claude.ai/artifact/Xc6BQCuJWw6uu5XDPeBnN7 |

Piece 1 notes. `template.html` holds the page; `frames.json` holds four YouTube preview frames per clip (thumbnail plus YouTube's automatic frames at 25, 50 and 75 percent), cropped to 16:9 and stored as data URIs; `build.py` writes `index.html`. The page cannot embed video, so each clip is a looping four-frame strip with a link to YouTube. The Butler figures (1 in 625 ear only, 1 in 94 graze, 1 in 110 at his actual turn, 6% of the speech as lucky) are quoted from `butler-shooting/results/RESULTS.md` and `results/speech_luck.json`; the page computes only 1 − (1 − 1/625)^N.
