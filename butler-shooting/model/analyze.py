"""Turn the pose sweep into the headline numbers and the article charts.

Reads results/rows/*.json (or results/sweep.json) and results/maps/*.npz; writes
results/summary.json and figures/*.png.

Logic
  1. P(outcome | pose) for one head-aimed shot comes straight from the sweep (Sam, 2026-10-13:
     analyse a head-aimed shot only).
  2. Outcomes (sim3d.py): "grazed" = the ear and/or only the outer GRAZE_DEPTH_MM of skin, the
     headline; "ear only" (the actual wound) is reported as a subset; "killed or wounded"; "arm";
     "miss".
  3. Head pose. rel = the angle between where his face pointed and the rifle (0 = facing it,
     90 = right ear toward it, roughly facing the crowd; negative = turned past it). Two estimates:
       wound only: uniform over rel in [-60, 90], weighted by P(right-ear-only hit | rel);
       video + wound: the video thread's measured rel (pose_handoff.json, a normal with its
       mean and sd) weighted by the same wound likelihood. This is the headline.
     Pitch: the sweep's pitches (-10..20) are averaged with equal weight where they exist.
  4. "How much the angle helped": the same shot with his head facing the crowd (rel 90) vs. at
     the estimated pose.
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import sys
sys.path.insert(0, str(Path(__file__).parent))
from sim3d import GRAZE_DEPTH_MM  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"
FIG = ROOT / "figures"
POSE = Path("/mnt/project-files/butler-shooting/video/pose_handoff.json")

BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
GREY = "#9a9890"
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e6e5e1", "#fcfcfb"
KEYS = ("grazed", "ear_only", "killed_or_wounded", "arm", "miss")


def load():
    rows_dir = RES / "rows"
    if rows_dir.exists() and any(rows_dir.glob("*.json")):
        return [json.loads(p.read_text()) for p in sorted(rows_dir.glob("*.json"))]
    return json.loads((RES / "sweep.json").read_text())


def style(ax):
    for s in ("top", "right", "left", "bottom"):
        ax.spines[s].set_visible(False)
    ax.tick_params(colors=INK2, length=0)
    ax.yaxis.grid(True, color=GRID, lw=1)
    ax.set_axisbelow(True)
    ax.set_facecolor(SURF)


def by_rel(rows, key, roll=0.0, lo=-60, hi=90, field="head"):
    """Average a per-row quantity over the swept pitches at each rel (equal pitch weights)."""
    rels = sorted({r["rel"] for r in rows if r["roll"] == roll and lo <= r["rel"] <= hi})
    vals = [np.mean([key(r[field]) for r in rows if r["roll"] == roll and r["rel"] == x]) for x in rels]
    return np.array(rels), np.array(vals)


def video_pose():
    if not POSE.exists():
        return None
    y = json.loads(POSE.read_text())["pose_relative_to_rifle"]["yaw"]
    return dict(mean=float(y["mean"]), sd=float(y["sd"]), file_mtime=POSE.stat().st_mtime)


def outcome_row(b):
    return {k: float(b[k]) for k in KEYS}


def posterior(rows, prior_kind):
    rels, like = by_rel(rows, lambda h: h["codes"]["ear_only_right"])
    if prior_kind == "video":
        v = video_pose()
        prior = np.exp(-0.5 * ((rels - v["mean"]) / v["sd"]) ** 2)
    else:
        prior = np.ones_like(like)
    prior = prior / prior.sum()
    post = prior * like
    return rels, prior, like, post / post.sum()


def summarize(rows, prior_kind):
    rels, prior, like, post = posterior(rows, prior_kind)
    b = {k: by_rel(rows, lambda h, k=k: h["buckets"][k])[1] for k in KEYS}
    fu = {k: by_rel(rows, lambda h, k=k: h["buckets"][k], field="head_followup")[1] for k in KEYS}
    cdf = np.cumsum(post)
    return dict(
        given_estimated_pose={k: float(post @ v) for k, v in b.items()},
        followup_shot_given_estimated_pose={k: float(post @ v) for k, v in fu.items()},
        prior_only={k: float(prior @ v) for k, v in b.items()},
        posterior_rel_mean=float(post @ rels),
        posterior_rel_90pct=[float(rels[np.searchsorted(cdf, 0.05)]), float(rels[np.searchsorted(cdf, 0.95)])],
        posterior_by_rel=dict(zip(map(float, rels), map(float, post))),
    )


def main():
    rows = load()
    FIG.mkdir(exist_ok=True)
    flat = {r["rel"]: r for r in rows if r["pitch"] == 0 and r["roll"] == 0}
    summary = dict(
        graze_depth_mm=GRAZE_DEPTH_MM,
        aim="head",
        video_pose=video_pose(),
        wound_only=summarize(rows, "flat"),
        video_and_wound=summarize(rows, "video") if video_pose() else None,
        facing_crowd_rel90=outcome_row(flat[90.0]["head"]["buckets"]),
        face_toward_rifle_rel0=outcome_row(flat[0.0]["head"]["buckets"]),
    )
    head = summary["video_and_wound"] or summary["wound_only"]
    summary["headline"] = dict(
        basis="video_and_wound" if summary["video_and_wound"] else "wound_only",
        **head["given_estimated_pose"],
        angle_lift_grazed=head["given_estimated_pose"]["grazed"] / summary["facing_crowd_rel90"]["grazed"],
    )
    (RES / "summary.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps({k: summary[k] for k in ("headline", "facing_crowd_rel90", "face_toward_rifle_rel0")}, indent=1))
    chart_curve(rows, head)
    chart_bars(summary, head)
    chart_map(head)


def chart_curve(rows, head):
    """Chance that one head-aimed shot only grazes him, and only hits the ear, by head turn."""
    fig, ax = plt.subplots(figsize=(10, 5.4), facecolor=SURF)
    sel = sorted([r for r in rows if r["roll"] == 0.0 and r["pitch"] == 0.0], key=lambda r: r["rel"])
    x = np.array([r["rel"] for r in sel])
    lo, hi = head["posterior_rel_90pct"]
    ax.axvspan(lo, hi, color="#f1f0ec", zorder=0, lw=0)
    gr = np.array([100 * r["head"]["buckets"]["grazed"] for r in sel])
    ear = np.array([100 * r["head"]["buckets"]["ear_only"] for r in sel])
    ax.plot(x, gr, color=AQUA, lw=2, solid_capstyle="round")
    ax.plot(x, ear, color=BLUE, lw=2, solid_capstyle="round")
    top = gr.max() * 1.15
    ax.set_ylim(0, top)
    arrow = dict(arrowstyle="-", color=INK2, lw=0.8, shrinkA=2, shrinkB=6)
    i = int(np.argmax(gr))
    ax.annotate(f"Grazed, not lethal (ear, or only the outer {GRAZE_DEPTH_MM:.0f} mm of skin)",
                (x[i], gr[i]), xytext=(48, 0.97 * top), color=INK, fontsize=10, va="center", arrowprops=arrow)
    j = int(np.argmax(ear))
    ax.annotate(f"Hit on the ear only, like the real wound: up to {ear[j]:.2f}%", (x[j], ear[j]),
                xytext=(48, 0.62 * top), color=INK, fontsize=10, va="center", arrowprops=arrow)
    k90 = int(np.where(x == 90)[0][0])
    ax.plot(x[k90], gr[k90], "o", ms=8, color=AQUA, mec=SURF, mew=2, zorder=5)
    ax.annotate(f"Facing the crowd: {gr[k90]:.1f}%", (x[k90], gr[k90]), xytext=(100, 0.30 * top), color=INK2,
                fontsize=9.5, va="center", arrowprops=arrow)
    ax.text((lo + hi) / 2, 0.03 * top, "His likely head turn\n(video and wound)", ha="center", va="bottom",
            color=INK2, fontsize=9)
    ax.set_xticks([-60, -30, 0, 30, 60, 90, 120, 150, 180])
    ax.set_xticklabels(["60° past\nthe rifle", "30° past", "0°\nface toward\nthe rifle", "30° short", "60° short",
                        "90°\nright ear toward\nthe rifle", "120°", "150°", "180°\nback of head\ntoward the rifle"])
    ax.set_xlim(-60, 180)
    ax.set_ylabel("Chance one head-aimed shot does this (%)", color=INK2)
    ax.set_title("Turning toward the rifle roughly doubled his chance of being merely grazed",
                 loc="left", color=INK, fontsize=12)
    style(ax)
    fig.savefig(FIG / "ear_only_vs_head_turn.png", dpi=150, bbox_inches="tight", facecolor=SURF)
    plt.close(fig)


def chart_bars(summary, head):
    """Stacked bars: one head-aimed shot as he stood, vs. the same shot with him facing the crowd."""
    segs = [("ear_only", "Ear only", BLUE), ("skin", f"Skin graze ({GRAZE_DEPTH_MM:.0f} mm or less)", AQUA),
            ("killed_or_wounded", "Killed or seriously wounded", ORANGE), ("arm", "Arm", GREY), ("miss", "Miss", YELLOW)]
    cases = [("As he stood\n(face toward the rifle)", head["given_estimated_pose"]),
             ("Had he faced the crowd\n(right ear toward the rifle)", summary["facing_crowd_rel90"])]
    fig, ax = plt.subplots(figsize=(10.5, 3.4), facecolor=SURF)
    for i, (lab, p) in enumerate(cases):
        vals = dict(p, skin=p["grazed"] - p["ear_only"])
        left = 0.0
        for k, name, col in segs:
            w = 100 * vals[k]
            ax.barh(i, w, left=left, height=0.42, color=col, edgecolor=SURF, lw=2, label=name if i == 0 else None)
            if w > 7:
                ax.text(left + w / 2, i, f"{w:.0f}%", ha="center", va="center",
                        color="white" if col in (BLUE, ORANGE) else INK, fontsize=10)
            left += w
        ax.text(101.5, i, f"grazed: {100 * p['grazed']:.1f}%\n(ear only: {100 * p['ear_only']:.2f}%)",
                va="center", color=INK, fontsize=9.5)
    ax.set_yticks(range(len(cases)))
    ax.set_yticklabels([c[0] for c in cases], color=INK)
    ax.invert_yaxis()
    ax.set_xlim(0, 125)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.set_xlabel("What one head-aimed shot does to him", color=INK2)
    g = 100 * head["given_estimated_pose"]["grazed"]
    one_in = int(round(100 / g))
    ax.set_title(f"About 1 shot in {one_in} would merely graze him, as Crooks's first shot did",
                 loc="left", color=INK, fontsize=12, pad=28)
    style(ax)
    ax.yaxis.grid(False)
    ax.xaxis.grid(True, color=GRID, lw=1)
    ax.legend(frameon=False, ncol=5, loc="lower left", bbox_to_anchor=(0.0, 1.0), fontsize=9, handlelength=1.2)
    fig.savefig(FIG / "outcome_bars.png", dpi=150, bbox_inches="tight", facecolor=SURF)
    plt.close(fig)


def chart_map(head):
    """Outcome map at the most likely pose: what a bullet on each path would do."""
    from matplotlib.colors import ListedColormap
    import matplotlib.patches as mpatches
    rel = 10 * round(head["posterior_rel_mean"] / 10)
    z = np.load(RES / "maps" / f"map_rel{rel:+04.0f}_p+00_r+00.npz", allow_pickle=True)
    codes = list(z["codes"])
    palette = {"miss": SURF, "miss_hair": "#f3e3a0", "ear_only_right": BLUE, "ear_only_left": BLUE,
               "graze_skin": AQUA, "arm": GREY, "brain": "#b3406a", "vessel": "#d0312d", "bone": "#c9c3b3",
               "airway": "#7fb2c9", "eye": "#3c3c3c", "torso": GREY, "deep_soft": "#eb9a70"}
    cmap = ListedColormap([palette[c] for c in codes])
    fig, ax = plt.subplots(figsize=(7, 9), facecolor=SURF)
    ax.imshow(z["fine"], origin="lower", cmap=cmap, vmin=0, vmax=len(codes) - 1, interpolation="nearest",
              extent=[z["fu"][0], z["fu"][-1], z["fv"][0], z["fv"][-1]])
    ax.plot(*z["aim_head"], marker="+", color=INK, ms=14, mew=2)
    ax.set_xlim(z["fu"][0], z["fu"][-1])
    ax.set_ylim(z["fv"][0], z["fv"][-1])
    ax.set_xlabel("mm, shooter's right →", color=INK2)
    ax.set_ylabel("mm, up →", color=INK2)
    ax.tick_params(colors=INK2)
    ax.set_title("Seen from the rifle, the bullet paths that merely graze him (blue and green)\n"
                 f"are thin rims around a target that is mostly fatal. Face turned {rel:.0f}° from the rifle;\n"
                 "the cross is the aim point.", loc="left", color=INK, fontsize=10)
    keys = [("ear only", BLUE), (f"skin graze ({GRAZE_DEPTH_MM:.0f} mm or less)", AQUA), ("brain", "#b3406a"),
            ("skull or spine", "#c9c3b3"), ("major vessel", "#d0312d"), ("airway", "#7fb2c9"),
            ("deeper soft tissue", "#eb9a70"), ("hair only (a miss)", "#f3e3a0"), ("torso", GREY)]
    ax.legend(handles=[mpatches.Patch(color=c, label=l) for l, c in keys], frameon=False, fontsize=8,
              loc="lower left", bbox_to_anchor=(1.0, 0.0))
    fig.savefig(FIG / "outcome_map_estimated_pose.png", dpi=150, bbox_inches="tight", facecolor=SURF)
    plt.close(fig)


if __name__ == "__main__":
    main()
