# Results of the 3D simulation (updated 2026-10-14, 3 mm graze rule)

## The headline

On July 13, 2024, Thomas Crooks fired his first shot at Donald Trump from a roof about 139 m away, and the bullet passed through the top of Trump's right ear without touching his skull. The headline asks how likely that was, given everything we model: Crooks's accuracy, Trump's anatomy, and the way Trump's head moved through his speech.

Suppose Crooks had fired one head-aimed shot at a random moment in the six and a half minutes of the speech before the first shot. Our simulation estimates that the shot would have hit only Trump's ear, as the real bullet did, about **1 in 990** times (0.10%). It would have merely grazed him, touching only the ear or the outer 3 mm of skin, about **1 in 105** times (0.95%). Whether the article quotes the ear-only figure or the wider graze figure is Sam's call, so both appear here.

On 2026-10-13 Sam chose 1 in 625 as the headline. That figure rested on a head track whose camera bearing was off by about 21°. On 2026-10-14 the "Opening scene" thread solved the RSBN camera's position against a model of the grounds, and the video thread re-measured the track with it. The corrected track shows Trump facing the crowd more of the time, so a shot at a random moment is less likely to find his ear standing clear, and the headline moved from 1 in 625 to 1 in 930. Fixing the range at the solved 139 m (see "The range" below) then moved it to 1 in 990.

With the camera solved, the video and the wound now agree about which way he faced, so the wound adds a correction of only about 1°. The video alone gives 1 in 980 for an ear-only hit and 1 in 105 for a graze.

The model follows only how far Trump turned his head, not how he nodded or tilted it. No one measured his nod and tilt frame by frame, so the speech figures average over the few nods we simulated near level (−10° to +20°), and this assumption is untested. Sam chose on 2026-10-13 not to run the extra poses. Judging by the poses already simulated, we expect that measured nod and tilt would move the ear-only headline by no more than about a fifth either way.

| Outcome of one head-aimed shot | At a random moment in the speech | At his actual turn when Crooks fired |
|---|---|---|
| Hits only the ear | 0.10% (1 in 990) | 0.75% (about 1 in 135) |
| Grazed, not lethal (ear or outer 3 mm of skin) | 0.95% (1 in 105) | 1.56% (1 in 64) |

Put another way, Crooks would have needed about 690 head-aimed shots at random moments of the speech for an even chance that one of them hit only the ear, and about 92 shots fired at Trump's actual turn.

### At his actual turn

At the moment Crooks fired, Trump had turned his face to within about 8° of the rifle line (on the short side), which made the odds much better for him. A head-aimed shot fired at that turn had a 1.56% chance (1 in 64) of merely grazing him and a 0.75% chance (about 1 in 135) of hitting the ear and nothing else. It had about a 29% chance of killing or seriously wounding him and a 70% chance of missing him.

| Outcome of one head-aimed shot at his actual turn | Chance |
|---|---|
| Grazed, not lethal | 1.56% |
| of which, the ear only | 0.75% |
| Killed or seriously wounded | 28.5% |
| Arm only | 0.03% |
| Miss | 69.9% |

At that turn the margin was slim. Our model puts the edge of the real bullet, which is 5.7 mm across, 6.1 mm from Trump's skull and 1.6 mm from the depth, 3 mm under the skin, at which a graze becomes a serious wound. Holding the same bullet path fixed while the head turns, the bullet would have gone deeper than 3 mm if his face had been turned 20° or more past the rifle, or between about 55° and 125° short of it, which includes facing the crowd. The bullet's edge would have touched the skull only if his face had been turned about 20° or more past the rifle (`assets/dashboard/margin_by_turn.json`).

### The range

The camera solve puts the rifle 139 m from Trump's head, with the bullet dropping 0.6° on its way. On 2026-10-14 we fixed the shot-spread model's range at 139 m; before that it drew the range anywhere from 125 m to 142 m, the spread of published estimates. At 139 m every shot spreads about 4% wider, so every hit, including grazes and ear-only hits, is about 6% less likely. We made the change by recounting the outcome maps from the full run, without new ray tracing: the 37 poses with a saved map were recounted exactly, and the rest were scaled by the same ratio, which varies by less than 1% across head turns. The 0.6° drop, against the 0.8° we assumed, shifts the bullet's path across the head by less than half a millimetre, which changes nothing.

Sam has not yet confirmed the 139 m range. If he prefers the earlier spread, these are the figures to restore; `model/dispersion.py` says how to switch back in one step, and the earlier rows are kept in `results/rows_range125_142/`.

| Figure | Range 125–142 m | Range 139 m (current) |
|---|---|---|
| Ear only, random moment in the speech | 0.11% (1 in 930) | 0.10% (1 in 990) |
| Graze, random moment in the speech | 1.01% (1 in 99) | 0.95% (1 in 105) |
| Ear only, at his actual turn | 0.79% | 0.75% |
| Graze, at his actual turn | 1.66% | 1.56% |
| Killed or seriously wounded / miss, at his actual turn | 29.6% / 68.7% | 28.5% / 69.9% |
| Shots for an even chance of an ear-only hit (speech / at his turn) | 650 / 87 | 690 / 92 |

### The real path at other head angles

Sam asked whether some other head angle would have put the real first bullet through Trump's skull. We held the bullet's real path fixed in space and moved the head through every turn from 60° past the rifle to the back of his head facing it, in 10° steps, each combined with nods from 20° chin-down to 20° chin-up and tilts of 15° either way (375 poses, `results/path_by_head_angle.json`, made by `model/path_angles.py`).

- **With his head level, the path enters bone only when he faces 20° or more past the rifle**, toward the chart screen. At every level turn from 10° past the rifle round to the back of his head, including facing the crowd, the bullet's edge clears the skull by about 5 to 11 mm. Those turns still cut more than 3 mm into the scalp at the back and side of the head.
- **A small nod changes that.** Facing the crowd, with his chin raised about 5°, the bullet's edge touches the skull; at about 8° the bullet's centre goes through bone; at about 12° it reaches the brain. Over the crowd-side turns (60° to 150° short of the rifle), a 10° chin-up nod puts the path through bone at 9 of 10 turns, and a 20° nod puts it through bone at all 10 and through the brain at 8. Lowering the chin moves the skull away from the path: at 10° chin-down it clears the bone by at least 13 mm.
- **A tilt does it too, sometimes.** Tilting the head 15° to either side, with no nod, puts the path through bone at 5 of the 10 crowd-side turns.

So Sam is right that such angles exist, but they need a nod or tilt as well as the turn. The video thread could not measure his nod or tilt, which is why the headline treats his head as level.

## What "grazed" means

Sam set the definition on 2026-10-13. A shot grazes Trump when the bullet touches only his ear, or only the outer 3 mm of skin anywhere on his head or neck, and goes no deeper. A bullet that reaches deeper soft tissue, bone, the brain, a major blood vessel, the airway, an eye or the torso counts as killing or seriously wounding him. A bullet that touches only hair counts as a miss.

We assume Crooks aimed at the middle of Trump's head. We no longer simulate a chest aim.

## How much the head turn helped him

Trump had turned his head to his right to look at a chart, which put his face nearly toward the rifle. Had he faced the crowd instead, his right ear would have pointed at the rifle, and a head-aimed shot would have grazed him only 0.84% of the time, and never hit the ear alone. The turn therefore nearly doubled his chance of being merely grazed (by a factor of 1.9), and it made an ear-only wound possible at all.

An ear-only hit is possible only when his face, or the back of his head, points within about 30° of the rifle. Within that range the ear stands clear of the skull as the gunman sees it. Turned further away, the ear lies over the skull, so a bullet through the ear goes on into his head.

## How unusual that head turn was

The video thread measured Trump's head turn five times a second from the RSBN broadcast over the six and a half minutes before the first shot (`video/pose_track.csv`, 1,599 usable frames). On 2026-10-14 it re-measured the track using the camera position solved by the "Opening scene" thread, which shifted every frame by about 21° toward facing the crowd. Through most of the speech he faced somewhere between the crowd and the rifle; his median turn put his face about 66° short of the rifle. He turned toward the rifle line mainly in the last 50 seconds, when he looked at the immigration chart.

The camera's remaining bearing error of about 12° shifts every frame of the track by the same amount, so we drew that shift once per trial and weighted it by how well it explains the ear-only wound. The wound now asks for a shift of only about 1°. With that weighting:

- A head-aimed shot fired at a random moment in the speech would have grazed him 0.95% of the time, against 1.56% at the moment of the first shot. His turn at the shot made a graze 1.6 times as likely as his average turn (90% range 1.3 to 1.8).
- An ear-only hit was about 8 times as likely at the shot as on average (0.75% against 0.10%).
- Only about 4% of the speech found him turned as favourably as he was at the first shot (90% range 1% to 8%).

The video alone, without the wound's weighting, now gives nearly the same answer: a graze 1.6 times as likely as average, with about 6% of the speech as favourable as the shot (90% range 1% to 18%). The video thread counts only 1 frame in 1,600 with a better chance of a right-ear-only hit than the moment he was hit. Its count uses its single best estimate of the camera bearing and the right ear alone; ours spreads the bearing over its uncertainty and counts a graze anywhere, so ours is the more cautious figure.

### The chart minute

The "Final turn" thread found that Trump's luck was concentrated in the last minute of the speech, after the border-crossing chart appeared on the big screen about 51 seconds before the shot (`open-questions/final-turn/README.md`). We recounted its figures from the same track and the same ear-only curve as the headline, with the same 1° wound shift. Here "within 35°" means his face pointed within 35° of the rifle line on either side, and every frame stands for the same fifth of a second.

- Before the chart went up, his face pointed within 35° of the rifle only 10% of the time, and it never came closer than about 10°.
- In the last 51 seconds, his face pointed within 35° of the rifle 96% of the time.
- Those 51 seconds are 13% of the speech, but they hold 71% of the speech's total chance of an ear-only hit. A head-aimed shot at a random moment in them had an average ear-only chance of 0.50%, against 0.031% in the earlier minutes, about 16 times as much.

The calculation is `model/speech_luck.py`; its output is `results/speech_luck.json` and the chart is `figures/head_turn_over_speech.png`.

## How we estimated which way he faced

We combined two pieces of evidence.

1. The RSBN broadcast camera, with its position solved against the scene model, puts Trump's face about 10° short of the rifle line at the first shot, give or take 12°. The video thread measured this; Sam dropped the pool camera because the microphone hid Trump's face in it.
2. The wound itself favours the head turns that make an ear-only hit likely.

Together they put his face about 8° short of the rifle, with a 90% range from 5° past it to 25° short of it. The wound alone, without the video, would put his face 7° short of the rifle and give a graze chance of 1.54% (ear only 0.72%). The two now agree.

## The follow-up shot

If Crooks had fired again at a Trump who stood still in the same pose, a second head-aimed shot would have grazed him 1.03% of the time and hit only the ear 0.50% of the time. These numbers are lower because a shot fired less than a second after the previous one scatters about 1.5 times as widely, based on the same marksmanship data.

## What the model contains

- **Head:** a 3D likeness of Trump by the Sketchfab artist shortlan, scaled to the head size of a 6-foot-1 man over 50.
- **Anatomy:** the BodyParts3D skull, brain, blood vessels, spine and airway, fitted inside the likeness about 6 mm under the skin. A second surface 3 mm under the skin marks where a graze ends.
- **Bullet:** each simulated bullet is traced through the head as a cylinder 5.7 mm across.
- **Shot spread:** comes from published marksmanship data for soldiers firing red-dot rifles, scaled to the range. Half of all head-aimed shots land within about 19 cm of the aim point.
- **Poses:** the full run covered 256 head poses, turning from 60° past the rifle to the back of the head toward it, with a range of nods and tilts.

The earlier ear-only run, which predates the graze rule and simulated both a head and a chest aim, is archived as `sweep_v1.json`, `rows_v1_earonly_2aims/` and `maps_v1/`.

The figures are in /mnt/project-files/butler-shooting/figures/, and the dashboard inputs are in /mnt/project-files/butler-shooting/assets/dashboard/.
