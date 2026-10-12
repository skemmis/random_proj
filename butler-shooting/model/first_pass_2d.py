"""First pass: dispersion model against a placeholder 2D silhouette.

The silhouette is a stand-in until the 3D head exists. It is what the shooter sees with
Trump's head turned partly toward him: head as an ellipse, neck and torso as boxes, and
an "ear only" strip where the right ear sticks out past the skull outline.
Units: cm, origin at head centre, x = shooter's right, y = up.
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from dispersion import moa_to_cm, sample_impacts  # noqa: E402

HEAD_HALF_W, HEAD_HALF_H = 8.0, 12.0
NECK = dict(x0=-6.0, x1=6.0, y0=-22.0, y1=-9.0)
TORSO = dict(x0=-25.0, x1=25.0, y0=-60.0, y1=-22.0)
# Protruding rim of the right ear beyond the skull outline (about 1.2 cm wide, 6 cm tall).
EAR = dict(x0=HEAD_HALF_W - 0.3, x1=HEAD_HALF_W + 1.2, y0=-2.0, y1=4.0)
CHEST_AIM = (0.0, -35.0)
# Where shot 1 actually struck: top of the right ear, on the head's outline.
SHOT1_ACTUAL = (8.5, 3.0)


def in_box(p, b):
    return (p[:, 0] >= b["x0"]) & (p[:, 0] <= b["x1"]) & (p[:, 1] >= b["y0"]) & (p[:, 1] <= b["y1"])


def classify(p):
    head = (p[:, 0] / HEAD_HALF_W) ** 2 + (p[:, 1] / HEAD_HALF_H) ** 2 <= 1.0
    ear = in_box(p, EAR) & ~head
    neck = in_box(p, NECK) & ~head
    torso = in_box(p, TORSO)
    return dict(ear_only=ear, head_or_neck=head | neck, torso=torso & ~(head | neck),
                miss=~(ear | head | neck | torso))


def summarize(name, p):
    c = classify(p)
    print(f"\n{name}")
    for k, v in c.items():
        print(f"  {k:13s} {v.mean():7.3%}")
    return c


def main(out_dir):
    rng = np.random.default_rng(13072024)
    n = 2_000_000
    head_p, e = sample_impacts(n, rng, aim_xy_cm=(0.0, 0.0))
    chest_p, _ = sample_impacts(n, rng, aim_xy_cm=CHEST_AIM)
    summarize("Aim at head (shot 1)", head_p)
    summarize("Aim at chest (shot 1)", chest_p)

    # Sanity check: how unusual is the real shot-1 miss distance under each aim point?
    for name, aim, p in [("head", (0, 0), head_p), ("chest", CHEST_AIM, chest_p)]:
        d_actual = np.hypot(SHOT1_ACTUAL[0] - aim[0], SHOT1_ACTUAL[1] - aim[1])
        d_sim = np.hypot(p[:, 0] - aim[0], p[:, 1] - aim[1])
        # Density of landing within 2 cm of the real impact point: a likelihood for aim point.
        near = np.hypot(p[:, 0] - SHOT1_ACTUAL[0], p[:, 1] - SHOT1_ACTUAL[1]) < 2.0
        print(f"\nShot 1 vs {name} aim: real miss {d_actual:.1f} cm "
              f"(~{d_actual / moa_to_cm(1, 133):.1f} MOA); "
              f"{(d_sim >= d_actual).mean():.1%} of simulated shots miss by more; "
              f"P(within 2 cm of real impact) = {near.mean():.4%}")

    # Figure: both impact clouds over the silhouette.
    fig, axes = plt.subplots(1, 2, figsize=(11, 7), sharey=True)
    for ax, (title, p) in zip(axes, [("Aim at head", head_p), ("Aim at chest", chest_p)]):
        k = p[:4000]
        ax.scatter(k[:, 0], k[:, 1], s=2, alpha=0.35, color="#4a6fa5", lw=0)
        ax.add_patch(matplotlib.patches.Ellipse((0, 0), 2 * HEAD_HALF_W, 2 * HEAD_HALF_H,
                                                fill=False, lw=1.5, color="#333"))
        for b, col in [(NECK, "#333"), (TORSO, "#333"), (EAR, "#d1495b")]:
            ax.add_patch(matplotlib.patches.Rectangle((b["x0"], b["y0"]), b["x1"] - b["x0"],
                                                      b["y1"] - b["y0"], fill=b is EAR,
                                                      lw=1.5, color=col, alpha=0.9))
        ax.plot(*SHOT1_ACTUAL, marker="x", color="#d1495b", ms=10, mew=2)
        ax.set_title(title)
        ax.set_aspect("equal")
        ax.set_xlim(-60, 60)
        ax.set_ylim(-80, 50)
        ax.set_xlabel("cm (shooter's right +)")
    axes[0].set_ylabel("cm (up +)")
    fig.suptitle("First-pass shot clouds vs placeholder silhouette (red = ear-only strip, x = real shot 1)")
    out = Path(out_dir) / "first_pass_2d.png"
    fig.savefig(out, dpi=130, bbox_inches="tight")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
