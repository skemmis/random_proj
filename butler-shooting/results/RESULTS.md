# Results of the 3D simulation (2026-10-13, 3 mm graze rule)

## The headline

On July 13, 2024, Thomas Crooks fired his first shot at Donald Trump from a roof about 135 m away, and the bullet passed through the top of Trump's right ear without touching his skull. Our simulation estimates that a head-aimed shot like Crooks's first one, fired at Trump as he stood at that moment, had about a 1 in 57 chance (1.8%) of merely grazing him. It had a 0.90% chance, about 1 in 110, of doing exactly what the real bullet did: hitting the ear and nothing else.

The same shot had about a 29% chance of killing or seriously wounding Trump and a 69% chance of missing him.

| Outcome of one head-aimed shot | Chance |
|---|---|
| Grazed, not lethal | 1.76% |
| of which, the ear only | 0.90% |
| Killed or seriously wounded | 29.5% |
| Arm only | 0.02% |
| Miss | 68.8% |

## What "grazed" means

Sam set the definition on 2026-10-13. A shot grazes Trump when the bullet touches only his ear, or only the outer 3 mm of skin anywhere on his head or neck, and goes no deeper. A bullet that reaches deeper soft tissue, bone, the brain, a major blood vessel, the airway, an eye or the torso counts as killing or seriously wounding him. A bullet that touches only hair counts as a miss.

We assume Crooks aimed at the middle of Trump's head. We no longer simulate a chest aim.

## How much the head turn helped him

Trump had turned his head to his right to look at a chart, which put his face almost straight toward the rifle. Had he faced the crowd instead, his right ear would have pointed at the rifle, and a head-aimed shot would have grazed him only 0.88% of the time, and never hit the ear alone. The turn therefore roughly doubled his chance of being merely grazed (by a factor of 1.99), and it made an ear-only wound possible at all.

An ear-only hit is possible only when his face, or the back of his head, points within about 30° of the rifle. Within that range the ear stands clear of the skull as the gunman sees it. Turned further away, the ear lies over the skull, so a bullet through the ear goes on into his head.

## How unusual that head turn was

The video thread measured Trump's head turn five times a second from the RSBN broadcast over the six and a half minutes before the first shot (`video/pose_track.csv`, 1,630 usable frames). Through most of the speech he faced somewhere between the crowd and the rifle; his median turn put his face about 45° short of the rifle. He turned toward the rifle line mainly in the last 50 seconds, when he looked at the immigration chart.

The camera's bearing error of about 14° shifts every frame of the track by the same amount, so we drew that shift once per trial. The ear-only wound says the shift was most likely about 10° toward the rifle. With that correction:

- A head-aimed shot fired at a random moment in the speech would have grazed him 1.06% of the time, against 1.75% at the moment of the first shot. His turn at the shot made a graze 1.7 times as likely as his average turn (90% range 1.3 to 1.8).
- An ear-only hit was 6 times as likely at the shot as on average (0.89% against 0.16%).
- Only about 6% of the speech found him turned as favourably as he was at the first shot (90% range 1% to 19%).

The video alone, without the wound's correction, gives a weaker and much less certain answer: a graze 1.4 times as likely as average, with about 19% of the speech as favourable as the shot (90% range 2% to 59%). The wound sharpens the estimate because only a turn near the rifle line can produce it. That reasoning does lean on the very outcome whose luck we are measuring, so the article should quote the video-only figure alongside it.

The calculation is `model/speech_luck.py`; its output is `results/speech_luck.json` and the chart is `figures/head_turn_over_speech.png`.

## How we estimated which way he faced

We combined two pieces of evidence.

1. The RSBN broadcast camera puts Trump's face about 11° past the rifle line at the first shot, give or take 14°. The video thread measured this; Sam dropped the pool camera because the microphone hid Trump's face in it.
2. The wound itself favours the head turns that make an ear-only hit likely.

Together they put his face about 1° past the rifle, with a 90% range from 15° past it to 15° short of it. The wound alone, without the video, would put his face 7° short of the rifle and give a graze chance of 1.63% (ear only 0.76%).

## The follow-up shot

If Crooks had fired again at a Trump who stood still in the same pose, a second head-aimed shot would have grazed him 1.16% of the time and hit only the ear 0.60% of the time. These numbers are lower because a shot fired less than a second after the previous one scatters about 1.5 times as widely, based on the same marksmanship data.

## What the model contains

- **Head:** a 3D likeness of Trump by the Sketchfab artist shortlan, scaled to the head size of a 6-foot-1 man over 50.
- **Anatomy:** the BodyParts3D skull, brain, blood vessels, spine and airway, fitted inside the likeness about 6 mm under the skin. A second surface 3 mm under the skin marks where a graze ends.
- **Bullet:** each simulated bullet is traced through the head as a cylinder 5.7 mm across.
- **Shot spread:** comes from published marksmanship data for soldiers firing red-dot rifles, scaled to the range. Half of all head-aimed shots land within about 18 cm of the aim point.
- **Poses:** the full run covered 256 head poses, turning from 60° past the rifle to the back of the head toward it, with a range of nods and tilts.

The earlier ear-only run, which predates the graze rule and simulated both a head and a chest aim, is archived as `sweep_v1.json`, `rows_v1_earonly_2aims/` and `maps_v1/`.

The figures are in /mnt/project-files/butler-shooting/figures/, and the dashboard inputs are in /mnt/project-files/butler-shooting/assets/dashboard/.
