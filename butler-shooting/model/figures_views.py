"""Article figures built from the shooter's-eye views in results/views/ (see views.py)."""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from views import view_path  # noqa: E402

FIG = Path(__file__).resolve().parents[1] / "figures"
BLUE, AQUA, ORANGE = np.array([42, 120, 214]) / 255, np.array([27, 175, 122]) / 255, np.array([235, 104, 52]) / 255
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e6e5e1", "#fcfcfb"


def painted(rel, pitch=0.0, alpha=0.75, show=("ear", "graze")):
    """The rendered likeness with ear-only zones in blue and skin-graze zones in aqua."""
    z = np.load(view_path(rel, pitch), allow_pickle=True)
    img = z["img"].copy()
    names = list(z["codes_names"])
    codes = z["codes"]
    bg = ~np.isfinite(z["depth"])
    img[bg] = np.array([0xfc, 0xfc, 0xfb]) / 255
    layers = []
    if "ear" in show:
        layers.append(([n for n in names if n.startswith("ear_only")], BLUE))
    if "graze" in show:
        layers.append(([n for n in names if n.startswith("graze")], AQUA))
    for group, col in layers:
        m = np.isin(codes, [names.index(n) for n in group])
        img[m] = (1 - alpha) * img[m] + alpha * col
    return img, z


if __name__ == "__main__":
    img, z = painted(0.0)
    plt.imsave(FIG / "_preview_view.png", img)


# ---------------------------------------------------------------------------------------------
import json  # noqa: E402

RES_DIR = Path(__file__).resolve().parents[1] / "results"
BLUE_HEX, AQUA_HEX, ORANGE_HEX = "#2a78d6", "#1baf7a", "#eb6834"


def sweep_rows():
    """Rows from the current sweep if it has run, else the first (ear-only, two-aim) sweep."""
    rows_dir = RES_DIR / "rows"
    if rows_dir.exists() and any(rows_dir.glob("*.json")):
        return [json.loads(p.read_text()) for p in sorted(rows_dir.glob("*.json"))], True
    return json.loads((RES_DIR / "sweep_v1.json").read_text()), False


def curve(rows, key):
    sel = sorted([r for r in rows if r["pitch"] == 0.0 and r["roll"] == 0.0], key=lambda r: r["rel"])
    return np.array([r["rel"] for r in sel]), np.array([100 * key(r) for r in sel])


def turn_label(rel):
    if rel == 0:
        return "face toward\nthe rifle"
    return f"{abs(rel):.0f}° {'short of' if rel > 0 else 'past'}\nthe rifle"


def style(ax):
    for s in ("top", "right", "left", "bottom"):
        ax.spines[s].set_visible(False)
    ax.tick_params(colors=INK2, length=0)
    ax.yaxis.grid(True, color=GRID, lw=1)
    ax.set_axisbelow(True)
    ax.set_facecolor(SURF)


def crop(img, frac=0.78):
    """Trim the empty margin around the head (renders are 300 mm wide)."""
    h, w = img.shape[:2]
    c0 = int(w * (1 - frac) / 2)
    return img[: int(h * 0.86), c0: w - c0]


def fig_exposure_strip():
    """Renders of his head from the rifle at eight head turns, above the ear-only curve."""
    rows, new = sweep_rows()
    rels = [-30, -15, 0, 15, 30, 45, 60, 90]
    fig = plt.figure(figsize=(16, 9), facecolor=SURF)
    ax = fig.add_axes([0.06, 0.09, 0.9, 0.40])
    x, ear = curve(rows, lambda r: r["head"]["codes"]["ear_only_right"] + r["head"]["codes"]["ear_only_left"])
    ax.plot(x, ear, color=BLUE_HEX, lw=2, solid_capstyle="round")
    lab_y = {}
    if new:
        _, gr = curve(rows, lambda r: r["head"]["buckets"]["grazed"])
        ax.plot(x, gr, color=AQUA_HEX, lw=2, solid_capstyle="round")
        ax.text(x[-1] + 2, gr[-1], "Grazed, not lethal\n(ear or outer 4 mm of skin)", color=INK, fontsize=10, va="center")
    i = int(np.argmax(ear))
    ax.plot(x[i], ear[i], "o", ms=8, color=BLUE_HEX, mec=SURF, mew=2, zorder=5)
    ax.annotate(f"Hit on the ear only: {ear[i]:.2f}% at best", (x[i], ear[i]), xytext=(-14, 0),
                textcoords="offset points", color=INK, fontsize=10, va="center", ha="right")
    ax.set_xlim(-35, 95)
    ax.set_ylim(0, None)
    ax.set_xticks(rels)
    ax.set_xticklabels([turn_label(r) for r in rels], color=INK2, fontsize=9)
    ax.set_ylabel("Chance that one head-aimed shot does this (%)", color=INK2)
    style(ax)
    # The renders, one above each tick, with a hairline down to the axis.
    w = 0.104
    for r in rels:
        img, _ = painted(float(r))
        xf = 0.06 + 0.9 * (r + 35) / 130
        iax = fig.add_axes([xf - w / 2, 0.52, w, 0.36])
        iax.imshow(crop(img, 0.70))
        iax.axis("off")
        fig.add_artist(plt.Line2D([xf, xf], [0.495, 0.525], color=GRID, lw=1, transform=fig.transFigure))
    est = 7.0
    ax.axvline(est, color=INK2, lw=1, ls=(0, (4, 3)))
    ax.text(est + 1.5, ax.get_ylim()[1] * 0.06, "His estimated turn\nat the first shot", color=INK2, fontsize=9)
    fig.text(0.06, 0.955, "Seen from the rifle, his ear stands clear of his skull only when he faces nearly toward Crooks",
             fontsize=15, color=INK)
    fig.text(0.06, 0.900, "Each head is posed as Trump would have looked through Crooks's sight. Blue marks where a bullet "
             "would hit the ear and nothing else; green marks where it would only skim the skin.\n"
             "He had turned to his right, toward a chart; facing the crowd put his right ear toward the rifle (90° short of it).",
             fontsize=10.5, color=INK2)
    fig.savefig(FIG / "ear_exposure_by_head_turn.png", dpi=130, facecolor=SURF)
    plt.close(fig)


if __name__ == "__main__":
    fig_exposure_strip()


def by_rel_pitch_avg(rows, key, lo=-30, hi=90):
    rels = sorted({r["rel"] for r in rows if r["roll"] == 0.0 and lo <= r["rel"] <= hi})
    return np.array(rels), np.array([np.mean([key(r) for r in rows if r["roll"] == 0.0 and r["rel"] == x])
                                     for x in rels])


def video_pose():
    """The video thread's measured head turn at shot 1, in our rel convention, if it has delivered."""
    f = Path("/mnt/project-files/butler-shooting/video/pose_handoff.json")
    if not f.exists():
        return None
    y = json.loads(f.read_text())["pose_relative_to_rifle"]["yaw"]
    return dict(mean=float(y["mean"]), sd=float(y["sd"]))


def fig_inference():
    """Three stacked panels: prior over head turns, likelihood of his wound, posterior."""
    rows, _ = sweep_rows()
    rels, like = by_rel_pitch_avg(rows, lambda r: r["head"]["codes"]["ear_only_right"], lo=-60, hi=90)
    video = video_pose()
    if video:
        prior = np.exp(-0.5 * ((rels - video["mean"]) / video["sd"]) ** 2)
    else:
        prior = np.ones_like(like)
    prior = prior / prior.sum()
    post = prior * like
    post /= post.sum()
    mean = float(post @ rels)
    cdf = np.cumsum(post)
    lo90, hi90 = rels[np.searchsorted(cdf, 0.05)], rels[np.searchsorted(cdf, 0.95)]
    fig, axs = plt.subplots(3, 1, figsize=(12, 10), sharex=True, facecolor=SURF,
                            gridspec_kw=dict(hspace=0.55))
    bw = 4.0
    step1 = (f"1. The broadcast footage puts his face {abs(video['mean']):.0f}° past the rifle at the first shot, "
             f"give or take {video['sd']:.0f}°" if video else
             "1. Before we look at the wound, we treat every head turn from 30° past the rifle to 90° short of it as equally likely")
    titles = [
        step1,
        "2. Then we ask how often each turn would produce his actual wound: a bullet through the right ear and nothing else",
        (f"3. Combining the two puts his face almost straight at the rifle: within {max(abs(lo90), abs(hi90)):.0f}° "
         "either way, nine times in ten" if abs(mean) < 3 else
         f"3. Combining the two puts his face about {abs(mean):.0f}° {'short of' if mean > 0 else 'past'} the rifle"),
    ]
    data = [100 * prior, 100 * like, 100 * post]
    ylabels = ["Chance from the\nvideo (%)" if video else "Chance before (%)", "Chance of his wound\nper shot (%)", "Chance after (%)"]
    cols = ["#9a9890", BLUE_HEX, BLUE_HEX]
    for ax, t, y, yl, c in zip(axs, titles, data, ylabels, cols):
        ax.bar(rels, y, width=bw, color=c, edgecolor=SURF, lw=1)
        ax.set_title(t, loc="left", color=INK, fontsize=10.5)
        ax.set_ylabel(yl, color=INK2, fontsize=9)
        style(ax)
    axs[2].axvspan(lo90 - bw / 2, hi90 + bw / 2, color="#f1f0ec", zorder=0, lw=0)
    axs[2].text(hi90 + 4, max(data[2]) * 0.8, f"90% of the weight lies between\n{turn_label(lo90).replace(chr(10), ' ')} "
                f"and {turn_label(hi90).replace(chr(10), ' ')}", color=INK2, fontsize=9, va="top")
    ticks = [-60, -30, 0, 30, 60, 90]
    axs[2].set_xticks(ticks)
    axs[2].set_xticklabels([turn_label(r) for r in ticks], color=INK2, fontsize=9)
    axs[2].set_xlim(-62, 95)
    # Small renders on the likelihood panel, on transparent backgrounds so no bar is hidden.
    top = max(data[1])
    for r, xc, note in ((0, -45, "Face toward the rifle:\nthe ear stands clear"),
                        (45, 55, "45° short: the ear\nlies over the skull"),
                        (90, 80, "Facing the crowd:\nthe ear faces the rifle")):
        img, _ = painted(float(r), show=("ear",))
        z = np.load(view_path(float(r)))
        rgba = np.dstack([img, np.isfinite(z["depth"]).astype(float)])
        iax = axs[1].inset_axes([xc - 9, top * 0.32, 18, top * 1.0], transform=axs[1].transData)
        iax.imshow(crop(rgba, 0.70))
        iax.axis("off")
        axs[1].text(xc, top * 0.04, note, color=INK2, fontsize=8.5, va="bottom", ha="center")
    fig.text(0.125, 0.955, "How the video and the wound together tell us which way he was facing", fontsize=15, color=INK)
    fig.savefig(FIG / "head_turn_inference.png", dpi=130, facecolor=SURF, bbox_inches="tight")
    plt.close(fig)
    return mean, lo90, hi90


if __name__ == "__main__":
    print(fig_inference())


def fig_shot_cloud(rel=7.0, n=400, seed=7):
    """A cloud of simulated head-aimed shots over the posed head, coloured by what each would do."""
    from dispersion import PRIORS, moa_to_cm, sample_engagements
    z = np.load(view_path(rel, 0.0, 420.0), allow_pickle=True)
    E = float(z["extent"])
    img, _ = painted(rel, 0.0) if False else (None, None)
    img = z["img"].copy()
    img[~np.isfinite(z["depth"])] = np.array([0xfc, 0xfc, 0xfb]) / 255
    names = list(z["codes_names"])
    codes = z["codes"]
    for group, col in (([n_ for n_ in names if n_.startswith("ear_only")], BLUE), (["graze_skin"], AQUA)):
        m = np.isin(codes, [names.index(g) for g in group if g in names])
        img[m] = 0.25 * img[m] + 0.75 * col
    rng = np.random.default_rng(seed)
    e = sample_engagements(n, rng, PRIORS)
    xm = e["bx"] + rng.normal(0, 1, n) * e["sx"]
    ym = e["by"] + rng.normal(0, 1, n) * e["sy"]
    aim = np.array([z["aim"] @ z["right"], z["aim"] @ z["up"]])
    u = aim[0] + moa_to_cm(xm, e["range_m"]) * 10
    v = aim[1] + moa_to_cm(ym, e["range_m"]) * 10
    res = codes.shape[0]
    col_idx = np.clip(((u + E) / (2 * E) * (res - 1)).round().astype(int), 0, res - 1)
    row_idx = np.clip(((E - v) / (2 * E) * (res - 1)).round().astype(int), 0, res - 1)
    inside = (np.abs(u) <= E) & (np.abs(v) <= E)
    c = np.array([names[k] for k in codes[row_idx, col_idx]])
    c[~inside] = "miss"
    kind = np.where(np.char.startswith(c, "ear_only"), "ear",
                    np.where(c == "graze_skin", "graze",
                             np.where(np.isin(c, ["miss", "miss_hair"]), "miss",
                                      np.where(c == "arm", "arm", "killed"))))
    fig, ax = plt.subplots(figsize=(9, 7.6), facecolor=SURF)
    ax.imshow(img, extent=[-E, E, -E, E])
    styles = {"miss": dict(mfc="none", mec="#9a9890", label="Miss"),
              "killed": dict(mfc=ORANGE_HEX, mec=SURF, label="Kills or seriously wounds him"),
              "graze": dict(mfc=AQUA_HEX, mec=SURF, label="Skims the skin only"),
              "ear": dict(mfc=BLUE_HEX, mec=SURF, label="Hits the ear only"),
              "arm": dict(mfc="#9a9890", mec=SURF, label="Hits an arm")}
    counts = {k: int((kind == k).sum()) for k in styles}
    for k, st in styles.items():
        sel = kind == k
        if sel.any():
            ax.plot(u[sel], v[sel], "o", ms=6, mew=1.2, ls="none",
                    label=f"{st['label']}: {counts[k]}", **{k2: v2 for k2, v2 in st.items() if k2 != "label"})
    ax.plot(*aim, marker="+", color=INK, ms=16, mew=2)
    ax.set_xlim(-E * 0.85, E * 0.85)
    ax.set_ylim(-170, E)
    ax.axis("off")
    ax.legend(frameon=False, loc="upper left", fontsize=10, bbox_to_anchor=(0.0, 0.0), ncol=2)
    ax.set_title(f"{n} simulated head-aimed shots at Trump as he stood at the first shot.\n"
                 f"{counts['killed']} kill or seriously wound him, {counts['ear'] + counts['graze']} only graze him, "
                 f"and the rest miss.", loc="left", color=INK, fontsize=12)
    fig.savefig(FIG / "shot_cloud_estimated_pose.png", dpi=130, facecolor=SURF, bbox_inches="tight")
    plt.close(fig)
    return counts


if __name__ == "__main__":
    print(fig_shot_cloud())


def fig_top_down(rel=7.0):
    """From above: his head at the estimated turn, with the bullet's path through the right ear."""
    from figures_3d import likeness_layers, xray
    from render import render
    from sim3d import Scene, fire_direction
    z = np.load(view_path(rel), allow_pickle=True)
    names = list(z["codes_names"])
    E = float(z["extent"])
    rr, cc = np.nonzero(z["codes"] == names.index("ear_only_right"))
    res = z["codes"].shape[0]
    u = (cc.mean() / (res - 1)) * 2 * E - E
    v = E - (rr.mean() / (res - 1)) * 2 * E
    sc = Scene(90.0 - rel)
    d = fire_direction(90.0, 0.8)
    from sim3d import aim_points
    centre = aim_points(sc, d)["head"] + np.array([0, -25.0, 0])
    p = centre + u * z["right"] + v * z["up"]
    view, up = (0, -1, 0), (0, 0, 1)
    E2 = 135.0
    kw = dict(center=np.array([0, 0, 0.0]), extent=E2)
    torso = sc.meshes["torso"]
    head_only = [(m, c) for m, c in likeness_layers(sc) if m is not torso]
    img, depth = render(head_only, view, up=up, res=800, **kw)
    img[~np.isfinite(depth)] = np.array([0xfc, 0xfc, 0xfb]) / 255
    sc.meshes["torso"] = torso.copy()
    sc.meshes["torso"].vertices = sc.meshes["torso"].vertices + np.array([0, -5000.0, 0])  # out of view
    xr = xray(sc, view, up=up, res=800, alpha=0.30, **kw)
    bgmask = ~np.isfinite(render(head_only, view, up=up, res=800, **kw)[1])
    xr[bgmask] = np.array([0xfc, 0xfc, 0xfb]) / 255

    def proj(P):  # image right = his right (-x), image up = the way his torso faced (+z)
        P = np.asarray(P, float)
        return np.array([-P[..., 0], P[..., 2]])

    a0, a1 = proj(p - 170 * d), proj(p + 150 * d)  # from the rifle side to beyond the head
    fig, ax = plt.subplots(figsize=(9, 8.6), facecolor=SURF)
    ax.imshow(xr, extent=[-E2, E2, -E2, E2])
    ax.annotate("", xy=a1, xytext=a0, annotation_clip=False,
                arrowprops=dict(arrowstyle="-|>", color=BLUE_HEX, lw=2.5, mutation_scale=18))
    ax.set_xlim(-E2, E2)
    ax.set_ylim(-E2, E2)
    ax.axis("off")
    yaw = np.radians(90.0 - rel)
    face_dir = proj(np.array([-np.sin(yaw), 0, np.cos(yaw)]))
    ax.annotate("", xy=face_dir * 130, xytext=face_dir * 105, annotation_clip=False,
                arrowprops=dict(arrowstyle="-|>", color=INK2, lw=1.2))
    ax.text(face_dir[0] * 118, face_dir[1] * 118 + 10, "His face", color=INK2, fontsize=10, ha="center")
    ax.annotate("", xy=(-115, 130), xytext=(-115, 100), annotation_clip=False,
                arrowprops=dict(arrowstyle="-|>", color=INK2, lw=1.2))
    ax.text(-108, 116, "Toward the crowd", color=INK2, fontsize=10, va="center")
    ax.text(a0[0], a0[1] + 8, "Bullet from Crooks's rifle,\n135 m away", color=INK, fontsize=10, ha="right",
            va="bottom")
    ax.text(-125, -125, "Seen from above, skin made see-through. The red shape at the bottom is his right ear.",
            color=INK2, fontsize=9.5)
    ax.set_title(f"With his face about {rel:.0f}° from the rifle, a bullet can pass\nthrough his right ear "
                 "without touching his skull", loc="left", color=INK, fontsize=13)
    fig.savefig(FIG / "top_down_bullet_path.png", dpi=120, facecolor=SURF, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    fig_top_down()
