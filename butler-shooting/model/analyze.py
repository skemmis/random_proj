"""Turn the pose sweep into the headline numbers and the article charts.

Reads results/sweep.json and results/maps/*.npz, writes results/summary.json and figures/*.png.

Logic
  1. P(outcome | pose, aim) comes straight from the sweep.
  2. Pose prior: Trump's torso faced the crowd with the shooter at about his 3 o'clock, and he
     had turned his head to his right toward the chart by some unknown amount. We take head yaw
     uniform on 0-120 deg (rel = 90 - yaw, i.e. -30..90), pitch uniform over {-10, 0, +10, +20}
     where swept (0 elsewhere), roll 0.
  3. What actually happened (a bullet through the top of the right ear, missing the skull) is
     only possible in some poses. Weighting the prior by P(right-ear-only hit | pose) gives the
     poses consistent with the wound; that posterior is our best estimate of his real pose.
  4. Headline: P(ear-only) for a fresh shot 1 fired at Trump in that estimated pose. Also
     reported: the pose-averaged prior value, and the head/chest aim split, plus a combined
     figure weighting aims by how well each explains the observed hit (equal prior odds).
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"
FIG = ROOT / "figures"

BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e6e5e1"
OUTCOMES = [("ear_only", "Ear only (the headline)", BLUE), ("killed_or_maimed", "Killed or maimed", ORANGE),
            ("other_minor", "Other minor wound", AQUA), ("miss", "Miss", YELLOW)]


def load():
    if (RES / "sweep.json").exists():
        return json.loads((RES / "sweep.json").read_text())
    return [json.loads(p.read_text()) for p in sorted((RES / "rows").glob("*.json"))]


def style(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=INK2)
    ax.yaxis.grid(True, color=GRID, lw=1)
    ax.set_axisbelow(True)


def by_rel(rows, key, roll=0.0, lo=-30, hi=90):
    """Average a per-row quantity over the swept pitches at each rel (uniform pitch prior)."""
    rels = sorted({r["rel"] for r in rows if r["roll"] == roll and lo <= r["rel"] <= hi})
    vals = []
    for rel in rels:
        rr = [r for r in rows if r["roll"] == roll and r["rel"] == rel]
        vals.append(np.mean([key(r) for r in rr]))
    return np.array(rels), np.array(vals)


def pose_posterior(rows, aim):
    """Uniform prior over rel in [-30, 90]; likelihood = P(right-ear-only hit | pose, aim)."""
    rels, like = by_rel(rows, lambda r: r[aim]["codes"]["ear_only_right"])
    prior = np.ones(len(rels)) / len(rels)
    post = prior * like
    return rels, prior, post / post.sum(), like


def main():
    rows = load()
    FIG.mkdir(exist_ok=True)
    summary = {}
    for aim in ("head", "chest"):
        rels, prior, post, like = pose_posterior(rows, aim)
        b = {k: by_rel(rows, lambda r, k=k: r[aim]["buckets"][k])[1] for k, _, _ in OUTCOMES}
        ear = b["ear_only"]
        summary[aim] = dict(
            given_estimated_pose={k: float(post @ v) for k, v in b.items()},
            averaged_over_prior_poses={k: float(prior @ v) for k, v in b.items()},
            best_single_pose={k: float(v[np.argmax(ear)]) for k, v in b.items()},
            best_single_pose_rel=float(rels[np.argmax(ear)]),
            evidence_right_ear_hit=float(prior @ like),
            posterior_rel_mean=float(post @ rels),
            posterior_rel_90pct=[float(rels[np.searchsorted(np.cumsum(post[np.argsort(rels)]), q)])
                                 for q in (0.05, 0.95)],
        )
        summary[aim]["followup_shot_given_estimated_pose"] = {
            k: float(post @ by_rel(rows, lambda r, k=k: r[aim + "_followup"]["buckets"][k])[1]) for k, _, _ in OUTCOMES}
        summary[aim]["posterior_by_rel"] = dict(zip(map(float, rels), map(float, post)))
    # Aim weights from how well each explains the observed hit (equal prior odds).
    eh, ec = summary["head"]["evidence_right_ear_hit"], summary["chest"]["evidence_right_ear_hit"]
    w_head = eh / (eh + ec)
    summary["aim_weight_head"] = w_head
    summary["combined_given_estimated_pose"] = {
        k: w_head * summary["head"]["given_estimated_pose"][k] + (1 - w_head) * summary["chest"]["given_estimated_pose"][k]
        for k, _, _ in OUTCOMES}
    (RES / "summary.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary, indent=1))

    chart_curve(rows)
    chart_bars(summary)
    chart_map(rows, summary)


def chart_curve(rows):
    fig, ax = plt.subplots(figsize=(10, 5.2))
    for aim, col, lab in (("head", BLUE, "Aimed at his head"), ("chest", ORANGE, "Aimed at his chest")):
        sel = sorted([r for r in rows if r["roll"] == 0.0 and r["pitch"] == 0.0], key=lambda r: r["rel"])
        x = [r["rel"] for r in sel]
        y = [100 * r[aim]["buckets"]["ear_only"] for r in sel]
        ax.plot(x, y, color=col, lw=2, solid_capstyle="round", label=lab)
        i = int(np.argmax(y))
        ax.annotate(f"{y[i]:.2f}%", (x[i], y[i]), xytext=(6, 4), textcoords="offset points", color=INK, fontsize=10)
    ax.axvspan(-30, 90, color="#f1f0ec", zorder=0)
    ax.text(30, ax.get_ylim()[1] * 0.93, "plausible head turns (0–120° to his right)", ha="center", color=INK2, fontsize=10)
    ax.set_xticks([-60, -30, 0, 30, 60, 90, 120, 150, 180])
    ax.set_xticklabels(["-60°", "-30°", "0°\nface to\nshooter", "30°", "60°", "90°\nright ear to\nshooter",
                        "120°", "150°", "180°\nback of head\nto shooter"])
    ax.set_ylabel("Chance one shot is ear-only (%)", color=INK2)
    ax.set_title("A survivable ear hit is only possible when his face (or the back of his head) points near the rifle",
                 loc="left", color=INK, fontsize=12)
    style(ax)
    ax.legend(frameon=False, loc="upper right")
    fig.savefig(FIG / "ear_only_vs_head_turn.png", dpi=150, bbox_inches="tight", facecolor="#fcfcfb")
    plt.close(fig)


def chart_bars(summary):
    cases = [("Aimed at head", summary["head"]["given_estimated_pose"]),
             ("Aimed at chest", summary["chest"]["given_estimated_pose"]),
             ("Best guess\n(aim weighted)", summary["combined_given_estimated_pose"])]
    fig, ax = plt.subplots(figsize=(10, 3.6))
    for i, (lab, p) in enumerate(cases):
        left = 0.0
        for k, name, col in OUTCOMES:
            w = 100 * p[k]
            ax.barh(i, w, left=left, height=0.5, color=col, edgecolor="#fcfcfb", lw=2,
                    label=name if i == 0 else None)
            if w > 6:
                ax.text(left + w / 2, i, f"{w:.0f}%", ha="center", va="center", color="white" if col in (BLUE, ORANGE) else INK,
                        fontsize=10)
            left += w
        ax.text(101, i, f"ear only: {100 * p['ear_only']:.2f}%", va="center", color=INK, fontsize=10)
    ax.set_yticks(range(len(cases)))
    ax.set_yticklabels([c[0] for c in cases])
    ax.invert_yaxis()
    ax.set_xlim(0, 125)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xlabel("Outcome of one shot fired at him in his estimated pose (%)", color=INK2)
    style(ax)
    ax.yaxis.grid(False)
    ax.legend(frameon=False, ncol=4, loc="lower center", bbox_to_anchor=(0.45, 1.0))
    fig.savefig(FIG / "outcome_bars.png", dpi=150, bbox_inches="tight", facecolor="#fcfcfb")
    plt.close(fig)


def chart_map(rows, summary):
    """Outcome map at the most likely pose, with the head-aim impact density."""
    from matplotlib.colors import ListedColormap
    rel = 10 * round(summary["head"]["posterior_rel_mean"] / 10)
    f = RES / "maps" / f"map_rel{rel:+04.0f}_p+00_r+00.npz"
    z = np.load(f, allow_pickle=True)
    codes = list(z["codes"])
    palette = {"miss": "#fcfcfb", "miss_hair": "#f3e3a0", "ear_only_right": BLUE, "ear_only_left": BLUE,
               "minor_scalp_neck": AQUA, "minor_arm": AQUA, "brain": "#b3406a", "vessel": "#d0312d",
               "bone": "#c9c3b3", "airway": "#7fb2c9", "eye": "#3c3c3c", "face": "#eb9a70", "torso": "#9a9890"}
    cmap = ListedColormap([palette[c] for c in codes])
    fig, ax = plt.subplots(figsize=(7, 9))
    ax.imshow(z["fine"], origin="lower", cmap=cmap, vmin=0, vmax=len(codes) - 1, interpolation="nearest",
              extent=[z["fu"][0], z["fu"][-1], z["fv"][0], z["fv"][-1]])
    ax.plot(*z["aim_head"], marker="+", color=INK, ms=14, mew=2)
    for r_moa, ls in ((3.2, "-"), (6.4, "--")):
        r_mm = r_moa * 39.3
        t = np.linspace(0, 2 * np.pi, 200)
        ax.plot(z["aim_head"][0] + r_mm * np.cos(t), z["aim_head"][1] + r_mm * np.sin(t), color=INK2, lw=1, ls=ls)
    ax.text(z["aim_head"][0] + 3.2 * 39.3 * 0.72, z["aim_head"][1] + 3.2 * 39.3 * 0.72, "1σ", color=INK2)
    ax.set_xlim(z["fu"][0], z["fu"][-1])
    ax.set_ylim(z["fv"][0], z["fv"][-1])
    ax.set_xlabel("mm, shooter's right →", color=INK2)
    ax.set_ylabel("mm, up →", color=INK2)
    ax.set_title(f"What each bullet path does, seen from the rifle\n(face turned {rel:.0f}° from the shooter; "
                 "blue = ear only)", loc="left", color=INK, fontsize=11)
    import matplotlib.patches as mpatches
    keys = [("ear only", BLUE), ("brain", "#b3406a"), ("skull/spine bone", "#c9c3b3"), ("major vessel", "#d0312d"),
            ("airway", "#7fb2c9"), ("face", "#eb9a70"), ("scalp/neck graze", AQUA), ("hair only (miss)", "#f3e3a0"),
            ("torso", "#9a9890")]
    ax.legend(handles=[mpatches.Patch(color=c, label=l) for l, c in keys], frameon=False, fontsize=8,
              loc="lower left", bbox_to_anchor=(1.0, 0.0))
    fig.savefig(FIG / "outcome_map_estimated_pose.png", dpi=150, bbox_inches="tight", facecolor="#fcfcfb")
    plt.close(fig)


if __name__ == "__main__":
    main()
