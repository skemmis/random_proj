# Results of the 3D simulation

Updated 2026-10-15. Graze rule: 3 mm. Range: 139 m.

## The headline

On July 13, 2024, Thomas Crooks fired at Donald Trump from a roof 139 m away. The first bullet passed through the top of Trump's right ear and missed his skull. How likely was that?

Suppose Crooks had fired one shot at Trump's head at a random moment in the six and a half minutes of speech before the first shot. That shot would have hit only his ear, as the real bullet did, about **1 time in 990** (0.10%). It would have merely grazed him, touching only the ear or the outer 3 mm of skin, about **1 time in 105** (0.95%). Sam will choose which figure the article leads with.

| One shot at his head | At a random moment in the speech | At his turn when Crooks fired |
|---|---|---|
| Hits only the ear | 0.10% (1 in 990) | 0.75% (about 1 in 135) |
| Grazes him (ear or outer 3 mm of skin) | 0.95% (1 in 105) | 1.56% (1 in 64) |

Crooks would have needed about 690 shots at random moments for an even chance of one ear-only hit, and about 92 shots at Trump's turn when he fired.

The headline has moved twice. Sam chose 1 in 625 on 2026-10-13, but the head track behind it used a camera bearing that was off by about 21°. Once we solved the camera's true position, the corrected track showed Trump facing the crowd more often, and the figure became 1 in 930. Fixing the range at the solved 139 m made it 1 in 990.

The video and the wound now agree on which way he faced; the wound shifts the track by only about 1°. The video alone gives 1 in 980 for an ear-only hit and 1 in 105 for a graze.

The model follows how far Trump turned his head, not how he nodded or tilted it. No one measured nod and tilt frame by frame, so the figures average over nods from 10° down to 20° up. Sam chose on 2026-10-13 not to simulate more. Judging by the poses we have, measured nods and tilts would move the ear-only figure by no more than a fifth either way.

### At his turn when Crooks fired

When Crooks fired, Trump's face pointed about **10° short of the rifle** (give or take 12°), as the camera shows. Pages quote this angle. The odds below average over our uncertainty about that turn, weighting each turn by how well it explains the ear-only wound. That weighting centres on 8° short; captions should not quote the 8°.

| One shot at his head, at his turn | Chance |
|---|---|
| Grazes him | 1.56% |
| of which, hits only the ear | 0.75% |
| Kills or seriously wounds him | 28.5% |
| Hits only an arm | 0.03% |
| Misses | 69.9% |

At exactly 10° the figures would be 1.64% for a graze and 0.82% for the ear alone.

**The margin was slim.** The bullet, 5.7 mm across, passed 6.1 mm from his skull and 1.6 mm from the depth of 3 mm at which a graze becomes a serious wound. Had the bullet flown the same line while his head was turned differently, it would have cut deeper than 3 mm with his face 20° or more past the rifle, or between 55° and 125° short of it, which includes facing the crowd. It would have touched the skull only with his face 20° or more past the rifle (`assets/dashboard/margin_by_turn.json`).

### The range

The camera solve puts the rifle 139 m from Trump's head, with the bullet dropping 0.6° on its way. Before 2026-10-14 the model drew the range from 125 m to 142 m, the spread of published estimates. At 139 m every shot spreads about 4% wider, so every kind of hit is about 6% less likely. We recounted the saved outcome maps rather than trace new rays: the 37 poses with a saved map exactly, the rest by the same ratio, which varies by less than 1% across head turns. The 0.6° drop, against the 0.8° we assumed, moves the path by less than half a millimetre.

Sam has not confirmed the 139 m range. To restore the earlier figures, follow the one-step switch in `model/dispersion.py`; the earlier rows are in `results/rows_range125_142/`.

| Figure | 125–142 m | 139 m (current) |
|---|---|---|
| Ear only, random moment | 0.11% (1 in 930) | 0.10% (1 in 990) |
| Graze, random moment | 1.01% (1 in 99) | 0.95% (1 in 105) |
| Ear only, at his turn | 0.79% | 0.75% |
| Graze, at his turn | 1.66% | 1.56% |
| Killed or seriously wounded / miss, at his turn | 29.6% / 68.7% | 28.5% / 69.9% |
| Shots for an even chance of an ear-only hit (random moment / at his turn) | 650 / 87 | 690 / 92 |

### The real path at other head angles

Sam asked whether another head angle would have put the real bullet through Trump's skull. We held the bullet's path fixed and moved the head through 375 poses: every turn from 60° past the rifle round to the back of his head, in 10° steps, with nods from 20° down to 20° up and tilts of 15° either way (`results/path_by_head_angle.json`, `model/path_angles.py`).

- **With his head level, the bullet reaches bone only when he faces 20° or more past the rifle**, toward the chart screen. At every other level turn, including facing the crowd, it clears the skull by 5 to 11 mm, though it still cuts more than 3 mm into the scalp.
- **A small nod changes that.** Facing the crowd, with his chin raised about 5°, the bullet's edge touches the skull; at 8° its centre goes through bone; at 12° it reaches the brain. Over the ten crowd-side turns (60° to 150° short of the rifle), a 10° nod puts the bullet through bone at nine, and a 20° nod puts it through bone at all ten and into the brain at eight. Lowering the chin moves the skull away: at 10° down the bullet clears bone by at least 13 mm.
- **A tilt does it sometimes.** With no nod, tilting his head 15° toward his left shoulder puts the bullet through bone at four of the ten crowd-side turns; tilting it toward his right shoulder, at one.

Such angles exist, then, but they need a nod or tilt as well as the turn. No one could measure his nod or tilt from the video, so the headline treats his head as level.

#### If his chin was raised at the shot

**Not quoted on any page.** On 2026-10-15 Sam chose to keep the level head, so the quoted margin stays 6.1 mm and 1.6 mm and the quoted odds stand.

Trump looks slightly up in the camera's frame at the shot. Matching the model to that frame puts his chin about 10° up; a separate estimate from the video puts it about 8° up, plausibly anywhere from 0° to 16° (`video/NOTES.md`, "Chin-up at shot 1"). We measured both ways the question can be asked, at his turn of 10° short of the rifle (`model/chin_up.py`, `results/chin_up_at_shot.json`).

| Chin up | Same line in space: gap to skull | Same line: gap to a serious wound | Through the ear wound: gap to skull | Through the ear wound: gap to a serious wound |
|---|---|---|---|---|
| 0° (level, quoted) | 6.1 mm | 1.6 mm | 6.1 mm | 1.7 mm |
| 3° | 5.7 mm | 1.2 mm | 5.8 mm | 1.4 mm |
| 5° | 5.4 mm | 0.9 mm | 5.8 mm | 1.3 mm |
| 8° | 4.8 mm | 0.4 mm | 5.6 mm | 1.1 mm |
| 10° | 4.5 mm | 0.1 mm | 5.6 mm | 1.0 mm |
| 12° | 4.2 mm | 0.3 mm too deep | 5.5 mm | 0.9 mm |
| 20° | 3.0 mm | 1.8 mm too deep | 6.1 mm | 1.6 mm |

- **Through the ear wound** is the reading that fits the real wound: at each nod we aimed the bullet at the middle of the ear-only zone, so it still clips the top of his ear. With his chin up 10°, the bullet passed 5.6 mm from his skull and 1.0 mm from a serious wound; at 8°, 5.6 mm and 1.1 mm. The margin narrows a little; the story holds.
- **The same line in space** asks what the level-head line would have done had he nodded. At 10° up it passes 4.5 mm from the skull and right at the 3 mm limit; beyond about 11° it cuts deeper. At this turn it reaches no bone at any nod up to 20°. The nods that put the bullet through bone need him facing the crowd.
- **The odds barely move.** With his chin up 10°, the full run's rows give 0.75% for the ear alone, 1.57% for a graze, 28.3% killed or seriously wounded and 70.1% a miss. Interpolated to 8°, they give 0.75%, 1.57%, 28.4% and 70.0%. The quoted figures already average over nods.

## What "grazed" means

Sam set the definition on 2026-10-13. A bullet grazes Trump when it touches only his ear, or only the outer 3 mm of skin on his head or neck. A bullet that reaches deeper soft tissue, bone, the brain, a major blood vessel, the airway, an eye or the torso kills or seriously wounds him. A bullet that touches only hair misses.

We assume Crooks aimed at the middle of Trump's head.

## How much the head turn helped him

Trump had turned his head to his right to look at a chart, which put his face nearly toward the rifle. Had he faced the crowd, his right ear would have pointed at the rifle; a shot at his head would have grazed him 0.84% of the time and never hit the ear alone. The turn nearly doubled his chance of a graze (1.9 times) and made an ear-only wound possible at all.

An ear-only hit is possible only when his face, or the back of his head, points within about 30° of the rifle. Then the ear stands clear of the skull as the gunman sees it. Turned further, the ear lies over the skull, and a bullet through the ear goes on into his head.

## How unusual that head turn was

We measured Trump's head turn five times a second from the camera over the six and a half minutes before the first shot (`video/pose_track.csv`, 1,599 usable frames). For most of the speech he faced somewhere between the crowd and the rifle; his median face angle was about 66° short of the rifle. He turned toward the rifle mainly in the last 50 seconds, when he looked at the immigration chart.

The camera's remaining bearing error, about 12°, shifts every frame by the same amount. We drew that shift once per trial and weighted it by how well it explains the wound, which asks for a shift of only about 1°. With that weighting:

- A shot at his head at a random moment would have grazed him 0.95% of the time, against 1.56% at his turn when Crooks fired: 1.6 times as likely at the shot (90% range 1.3 to 1.8).
- An ear-only hit was about 8 times as likely at the shot as on average (0.75% against 0.10%).
- Only about 4% of the speech found him turned as favourably as at the shot (90% range 1% to 8%).

The video alone gives nearly the same answer: a graze 1.6 times as likely as average, with about 6% of the speech as favourable as the shot (90% range 1% to 18%). Counting frames with a better chance of a right-ear-only hit, using the camera's single best bearing, finds 1 in 1,600. Our 4% spreads the bearing over its uncertainty and counts a graze anywhere, so it is the more cautious figure.

### The chart minute

Trump's luck was concentrated in his last minute, after the border-crossing chart went up on the big screen about 51 seconds before the shot (`open-questions/final-turn/README.md`). We recounted from the same track, with the same 1° shift. "Within 35°" means his face pointed within 35° of the rifle on either side.

- Before the chart went up, his face pointed within 35° of the rifle only 10% of the time, and never closer than about 10°.
- In the last 51 seconds, it pointed within 35° of the rifle 96% of the time.
- Those 51 seconds are 13% of the speech but hold 71% of its chance of an ear-only hit. A shot at a random moment in them had an ear-only chance of 0.50%, against 0.031% earlier, about 16 times as much.

The calculation is `model/speech_luck.py`; its output is `results/speech_luck.json` and its chart `figures/head_turn_over_speech.png`.

## How we estimated which way he faced

Two kinds of evidence, combined:

1. The camera puts Trump's face about 10° short of the rifle at the first shot, give or take 12°.
2. The wound favours the turns that make an ear-only hit likely.

Together they put his face about 8° short of the rifle (90% range 5° past to 25° short). That combined figure weights the odds at his turn; captions quote the camera's 10°, which the margin and the drawings also use. The wound alone would put his face 7° short and give a graze chance of 1.54% (ear only 0.72%).

## The follow-up shot

Had Crooks fired again at a Trump standing still in the same pose, a second shot would have grazed him 1.03% of the time and hit only the ear 0.50% of the time. A shot fired less than a second after the last one scatters about 1.5 times as widely, by the same marksmanship data.

## What the model contains

- **Head:** a 3D likeness of Trump by the Sketchfab artist shortlan, scaled to the head of a 6-foot-1 man over 50.
- **Anatomy:** the BodyParts3D skull, brain, blood vessels, spine and airway, fitted about 6 mm under the skin. A second surface 3 mm under the skin marks where a graze ends.
- **Bullet:** a cylinder 5.7 mm across, traced through the head.
- **Shot spread:** published marksmanship data for soldiers firing red-dot rifles, scaled to the range. Half of all shots at the head land within about 19 cm of the aim point.
- **Poses:** 256 head poses, from 60° past the rifle round to the back of the head, with a range of nods and tilts.

## Sources

- **Head track:** the RSBN broadcast of the rally, measured by the video thread (`video/pose_track.csv`, `video/NOTES.md`). Sam dropped the pool camera because the microphone hid Trump's face.
- **Camera position, range and screens:** the scene model's camera solve (`scene/camera_solve.json`).
- **The chart minute:** the final-turn thread (`open-questions/final-turn/README.md`).
- **Archive:** the earlier ear-only run, before the graze rule, with both head and chest aims, is in `sweep_v1.json`, `rows_v1_earonly_2aims/` and `maps_v1/`.

The figures are in `/mnt/project-files/butler-shooting/figures/`, and the dashboard inputs in `/mnt/project-files/butler-shooting/assets/dashboard/`.
