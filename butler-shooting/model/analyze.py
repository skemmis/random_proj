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

    chart_curve(rows, summary)
    chart_bars(summary)
    chart_map(rows, summary)


def chart_curve(rows, summary):
    """Line chart: chance that one shot is an ear-only hit, by how far his face was turned."""
    fig, ax = plt.subplots(figsize=(10, 5.4))
    fig.patch.set_facecolor("#fcfcfb")
    ax.set_facecolor("#fcfcfb")
    ax.axvspan(-30, 90, color="#f1f0ec", zorder=0, lw=0)
    peak = {}
    for aim, col, lab in (("head", BLUE, "Gunman aimed at his head"), ("chest", ORANGE, "Gunman aimed at his chest")):
        sel = sorted([r for r in rows if r["roll"] == 0.0 and r["pitch"] == 0.0], key=lambda r: r["rel"])
        x = np.array([r["rel"] for r in sel])
        y = np.array([100 * r[aim]["buckets"]["ear_only"] for r in sel])
        ax.plot(x, y, color=col, lw=2, solid_capstyle="round", solid_joinstyle="round")
        i = int(np.argmax(y))
        peak[aim] = (x[i], y[i])
        ax.plot(x[i], y[i], "o", ms=8, color=col, mec="#fcfcfb", mew=2, zorder=5)
        ymax_lab = {"head": 0.97, "chest": 0.20}[aim]
        peak[aim] = (x[i], y[i], ymax_lab, lab)
    top = max(v[1] for v in peak.values()) * 1.08
    ax.set_ylim(0, top)
    arrow = dict(arrowstyle="-", color=INK2, lw=0.8, shrinkA=2, shrinkB=6)
    for aim, (px, py, fy, lab) in peak.items():
        ax.annotate(f"{lab}: peaks at {py:.2f}%", (px, py), xytext=(48, fy * top), color=INK, fontsize=10,
                    va="center", arrowprops=arrow)
    est = summary["head"]["posterior_rel_mean"]
    ax.axvline(est, color=INK2, lw=1, ls=(0, (4, 3)))
    ax.annotate(f"His most likely head turn, about {est:.0f}°,\ninferred from where the bullet actually hit",
                (est, 0.66 * top), xytext=(48, 0.66 * top), color=INK2, fontsize=9, va="center", arrowprops=arrow)
    ax.text(62, 0.03 * top, "Head turns we consider plausible", ha="center", va="bottom", color=INK2, fontsize=9)
    ax.set_xticks([-60, -30, 0, 30, 60, 90, 120, 150, 180])
    ax.set_xticklabels(["-60°", "-30°", "0°\nface toward\ngunman", "30°", "60°", "90°\nright ear toward\ngunman",
                        "120°", "150°", "180°\nback of head\ntoward gunman"])
    ax.set_xlim(-60, 180)
    ax.set_ylabel("Chance one shot hits only the ear (%)", color=INK2)
    ax.set_title("A bullet can clip only his ear when his face, or the back of his head, points close to the rifle",
                 loc="left", color=INK, fontsize=12)
    style(ax)
    for sp in ("left", "bottom"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(length=0)
    fig.savefig(FIG / "ear_only_vs_head_turn.png", dpi=150, bbox_inches="tight", facecolor="#fcfcfb")
    plt.close(fig)


def chart_bars(summary):
    """Stacked bars: what one shot does to Trump in his estimated pose, for each aim point."""
    cases = [("Gunman aimed\nat his head", summary["head"]["given_estimated_pose"]),
             ("Gunman aimed\nat his chest", summary["chest"]["given_estimated_pose"]),
             ("Our best guess\n(both aims, weighted)", summary["combined_given_estimated_pose"])]
    fig, ax = plt.subplots(figsize=(10, 3.9))
    fig.patch.set_facecolor("#fcfcfb")
    ax.set_facecolor("#fcfcfb")
    for i, (lab, p) in enumerate(cases):
        left = 0.0
        for k, name, col in OUTCOMES:
            w = 100 * p[k]
            ax.barh(i, w, left=left, height=0.42, color=col, edgecolor="#fcfcfb", lw=2,
                    label=name if i == 0 else None)
            if w > 7:
                ax.text(left + w / 2, i, f"{w:.0f}%", ha="center", va="center",
                        color="white" if col in (BLUE, ORANGE) else INK, fontsize=10)
            left += w
        ax.text(101.5, i, f"ear only: {100 * p['ear_only']:.2f}%", va="center", color=INK, fontsize=10)
    comb = 100 * summary["combined_given_estimated_pose"]["ear_only"]
    ax.set_yticks(range(len(cases)))
    ax.set_yticklabels([c[0] for c in cases], color=INK)
    ax.invert_yaxis()
    ax.set_xlim(0, 122)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.set_xlabel("What one shot does to him, with his head turned as we estimate", color=INK2)
    one_in = 10 * round(100 / comb / 10)
    ax.set_title(f"About 1 shot in {one_in} would do what Crooks's first shot did: hit his ear and nothing else",
                 loc="left", color=INK, fontsize=12, pad=28)
    style(ax)
    ax.yaxis.grid(False)
    ax.xaxis.grid(True, color=GRID, lw=1)
    for sp in ("left", "bottom"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(length=0)
    ax.legend(frameon=False, ncol=4, loc="lower left", bbox_to_anchor=(0.0, 1.0), fontsize=9, handlelength=1.2)
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
    ax.set_title(f"Seen from the rifle, his ears (blue) are thin strips beside a skull that fills the target\n"
                 f"Each colour shows what a bullet on that path would hit, with his face turned {rel:.0f}° from the gunman.\n"
                 "The circles hold the typical spread of shots aimed at the cross.", loc="left", color=INK, fontsize=10)
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
