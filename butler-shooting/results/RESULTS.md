# Results of the 3D simulation (2026-10-13)

## The headline

On July 13, 2024, Thomas Crooks fired his first shot at Donald Trump from a roof about 135 m away, and the bullet passed through the top of Trump's right ear without touching his skull. Our simulation estimates that a shot like Crooks's first one had about a 1 in 150 chance (0.67%) of doing exactly that: hitting the ear and nothing else.

The same shot had about a 34% chance of killing or maiming Trump, a 63% chance of missing him, and a 1.5% chance of leaving some other minor wound, such as a graze to the scalp or neck.

## How the number depends on where Crooks aimed

We do not know whether Crooks aimed at Trump's head or his chest, so we simulated both.

| Where Crooks aimed | Ear only | Killed or maimed | Other minor wound | Miss |
|---|---|---|---|---|
| At the head | 0.76% | 29.0% | 1.5% | 68.7% |
| At the chest | 0.12% | 69.5% | 1.1% | 29.3% |
| Best guess, both aims weighted | 0.67% | 34.4% | 1.5% | 63.5% |

The best-guess row weights the two aims by how well each one explains the wound Trump actually received. A head-aimed shot is about 6.5 times more likely than a chest-aimed shot to produce a right-ear-only hit, so the best guess leans 87% toward a head aim.

## How the number depends on which way Trump faced

A bullet can hit only the ear when Trump's face, or the back of his head, points toward the rifle. In that position the ear sticks out beside the skull, as seen from the gunman. When Trump turns his head 40° or more from the rifle, his ear lies in front of his skull from the gunman's view, so any bullet that hits the ear goes on into his head.

No one has published how far Trump had turned his head when the first shot hit. We therefore let the wound itself tell us: we started with every head turn from 30° left to 120° right as equally plausible, then favoured the turns that make a right-ear-only hit likely. That puts his face about 7° from the rifle, with a 90% range from 10° one way to 25° the other.

## The follow-up shot

If Crooks had fired again at a Trump who stood still in the same pose, the second shot would have hit only the ear about 0.5% of the time with a head aim and 0.14% of the time with a chest aim. These numbers are lower because a shot fired less than a second after the previous one scatters about 1.5 times as widely, based on the same marksmanship data.

## What the model contains

- **Head:** a 3D likeness of Trump by the Sketchfab artist shortlan, scaled to the head size of a 6-foot-1 man over 50.
- **Anatomy:** the BodyParts3D skull, brain, blood vessels and airway, fitted inside the likeness about 6 mm under the skin.
- **Bullet:** each simulated bullet is traced through the head.
- **Shot spread:** comes from published marksmanship data for shooters like Crooks at this range.

The figures are in /mnt/project-files/butler-shooting/figures/.
