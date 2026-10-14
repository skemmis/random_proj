"""How unusual was his head angle at shot 1? Combine the video thread's whole-speech head track
(RSBN, 5 fps) with the sweep's outcome-by-turn curves. The track's 14 deg error is mostly one shared
camera-bearing offset, so we draw that offset once per sample, weighted by how well it explains the
wound (right ear only), and shift the whole track by it."""
import csv, json
from pathlib import Path
import numpy as np
from figures_views import sweep_rows, by_rel_pitch_avg

TRACK = Path("/mnt/project-files/butler-shooting/video/pose_track.csv")
OUT = Path(__file__).resolve().parent.parent / "results" / "speech_luck.json"

rows, _ = sweep_rows()
key = {"grazed": lambda r: r["head"]["buckets"]["grazed"],
       "ear_only": lambda r: r["head"]["buckets"]["ear_only"],
       "ear_right": lambda r: r["head"]["codes"]["ear_only_right"]}


def curves(level):
    out = {}
    for k, f in key.items():
        if level:
            sel = sorted([r for r in rows if r["pitch"] == 0.0 and r["roll"] == 0.0], key=lambda r: r["rel"])
            out[k] = (np.array([r["rel"] for r in sel]), np.array([f(r) for r in sel]))
        else:
            out[k] = by_rel_pitch_avg(rows, f, lo=-60, hi=180)
    return out


def run(level, n=4000, seed=7, use_wound=True):
    t, rel = [], []
    for r in csv.DictReader(TRACK.open()):
        if r["rel_deg"]:
            t.append(float(r["t_s"])); rel.append(float(r["rel_deg"]))
    t, rel = np.array(t), np.array(rel)
    shot_meas = json.loads(Path("/mnt/project-files/butler-shooting/video/pose_handoff.json").read_text()
                           )["pose_relative_to_rifle"]["yaw"]["mean"]
    pre = t < 0
    C = curves(level)
    f = {k: (lambda x, k=k: np.interp(x, *C[k])) for k in C}
    rng = np.random.default_rng(seed)
    sd = float(np.median([float(r["rel_sd_deg"]) for r in csv.DictReader(TRACK.open()) if r["rel_sd_deg"]]))
    e = rng.normal(0, sd, 40 * n)
    w = f["ear_right"](shot_meas + e) if use_wound else np.ones_like(e)  # wound likelihood of each offset
    e = rng.choice(e, n, p=w / w.sum())
    res = {k: [] for k in ("zone_share", "grazed_shot", "grazed_avg", "ear_shot", "ear_avg",
                           "grazed_pct_frames_higher", "ear_pct_frames_higher")}
    for ei in e:
        x, s = rel[pre] + ei, shot_meas + ei
        g, eo = f["grazed"](x), f["ear_only"](x)
        res["zone_share"].append(np.mean(eo > 0.0005))
        res["grazed_shot"].append(f["grazed"](s)); res["grazed_avg"].append(g.mean())
        res["ear_shot"].append(f["ear_only"](s)); res["ear_avg"].append(eo.mean())
        res["grazed_pct_frames_higher"].append(np.mean(g >= f["grazed"](s)))
        res["ear_pct_frames_higher"].append(np.mean(eo >= f["ear_only"](s)))
    R = {k: np.array(v) for k, v in res.items()}
    summ = lambda a: dict(mean=float(a.mean()), p05=float(np.quantile(a, .05)), p95=float(np.quantile(a, .95)))
    out = {k: summ(v) for k, v in R.items()}
    out["grazed_lift"] = summ(R["grazed_shot"] / R["grazed_avg"])
    out["ear_lift"] = summ(R["ear_shot"] / np.maximum(R["ear_avg"], 1e-9))
    out["frames"] = int(pre.sum()); out["span_s"] = [float(t[pre].min()), float(t[pre].max())]
    out["track_rel_median"] = float(np.median(rel[pre]))
    out["track_rel_quartiles"] = [float(np.quantile(rel[pre], q)) for q in (.25, .75)]
    out["offset_posterior_mean"] = float(e.mean())
    return out


def chart():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from figures_views import INK, INK2, GRID, SURF, BLUE_HEX, AQUA_HEX, FIG
    res = json.loads(OUT.read_text())["pitch_averaged"]
    off = res["offset_posterior_mean"]
    t, rel = [], []
    for r in csv.DictReader(TRACK.open()):
        if r["rel_deg"] and float(r["t_s"]) < 0:
            t.append(float(r["t_s"])); rel.append(float(r["rel_deg"]))
    t, rel = np.array(t) / 60, np.array(rel)
    C = curves(False)
    rel = rel + off  # corrected for the camera's bearing error, as the wound implies
    g = 100 * np.interp(rel, *C["grazed"])
    order = np.argsort(t)
    t, rel, g = t[order], rel[order], g[order]
    smooth = lambda y: np.array([np.median(y[max(0, i - 5):i + 6]) for i in range(len(y))])  # ~2 s
    breaks = np.nonzero(np.diff(t) > 1.0 / 60)[0] + 1  # cutaways: don't join across gaps over 1 s
    segs = lambda y: zip(np.split(t, breaks), np.split(smooth(y), breaks))
    fig, axs = plt.subplots(2, 1, figsize=(11, 7.4), sharex=True, facecolor=SURF,
                            gridspec_kw=dict(hspace=0.35))
    for ax in axs:
        ax.set_facecolor(SURF)
        for s in ax.spines.values():
            s.set_visible(False)
        ax.grid(axis="y", color=GRID, lw=0.8)
        ax.tick_params(colors=INK2, labelsize=9, length=0)
    x_lab = 0.08
    ax = axs[0]
    ax.axhspan(-15, 35, color="#e8f0fb", zorder=0)
    ax.text(x_lab, 10, "A bullet could hit\nonly his right ear", color=INK2, fontsize=9, va="center")
    ax.scatter(t, rel, s=3, color=BLUE_HEX, alpha=0.25, lw=0)
    for ts, ys in segs(rel):
        ax.plot(ts, ys, color=BLUE_HEX, lw=1.6)
    ax.axhline(90, color=INK2, lw=0.8, ls=(0, (2, 3)))
    ax.text(x_lab, 90, "Facing the crowd", color=INK2, fontsize=9, va="center")
    ax.set_ylim(-45, 135)
    ax.set_yticks([-30, 0, 30, 60, 90, 120])
    ax.set_yticklabels(["30° past", "face to rifle", "30° short", "60° short", "90° short", "120° short"])
    ax.invert_yaxis()
    ax.set_ylabel("His head turn,\nrelative to the rifle", color=INK2, fontsize=9)
    ax.set_title("1. Through the speech, he mostly faced between the crowd and the rifle", loc="left",
                 color=INK, fontsize=11)
    ax = axs[1]
    ax.scatter(t, g, s=3, color=AQUA_HEX, alpha=0.25, lw=0)
    for ts, ys in segs(g):
        ax.plot(ts, ys, color=AQUA_HEX, lw=1.6)
    avg, shot = 100 * res["grazed_avg"]["mean"], 100 * res["grazed_shot"]["mean"]
    ax.axhline(avg, color=INK2, lw=0.8, ls=(0, (2, 3)))
    ax.text(x_lab, avg, f"Speech\naverage:\n{avg:.2f}%", color=INK2, fontsize=9, va="center")
    ax.axhline(shot, color=INK, lw=0.8, ls=(0, (4, 3)))
    ax.text(x_lab, shot, f"At the\nfirst shot:\n{shot:.2f}%", color=INK, fontsize=9, va="center")
    ax.set_ylabel("Chance one head-aimed\nshot merely grazes him (%)", color=INK2, fontsize=9)
    pct = 100 * res["grazed_pct_frames_higher"]["mean"]
    ax.set_title(f"2. Only about {pct:.0f}% of the speech found him turned as luckily as at the first shot",
                 loc="left", color=INK, fontsize=11)
    ax.set_xlabel("Minutes before the first shot", color=INK2, fontsize=9)
    ax.set_xlim(t.min() - 0.05, 0.05)
    ax.set_xticks(range(-6, 1))
    ax.set_xticklabels([str(abs(x)) for x in range(-6, 1)])
    fig.text(0.125, 0.965, f"At the first shot, his head turn made a graze {res['grazed_lift']['mean']:.1f} times as "
             "likely as it was on average during his speech", fontsize=14, color=INK)
    fig.text(0.125, 0.0, "The video analysis read his head turn from the RSBN broadcast five times a second (dots; "
             "the line is a 2-second median, broken at cutaways).\nThe camera's bearing comes from the scene model's "
             f"camera solve; the ear-only wound adds a correction of only {abs(off):.0f}°, which is applied here.\n"
             "A graze means the bullet touched only the ear or the outer 3 mm of skin.",
             fontsize=8.5, color=INK2, va="top")
    fig.savefig(FIG / "head_turn_over_speech.png", dpi=150, facecolor=SURF, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    res = {"pitch_averaged": run(False), "level_head": run(True), "video_only_pitch_averaged": run(False, use_wound=False),
           "notes": __doc__}
    def quoted(r):
        pct = lambda x: "under 1%" if x < 0.005 else f"{100 * x:.0f}%"
        return {"share_of_speech_as_lucky": pct(r["grazed_pct_frames_higher"]["mean"]),
                "share_of_speech_as_lucky_90pct": [pct(r["grazed_pct_frames_higher"]["p05"]),
                                                   pct(r["grazed_pct_frames_higher"]["p95"])],
                "graze_lift": f"{r['grazed_lift']['mean']:.1f}x",
                "graze_lift_90pct": [f"{r['grazed_lift']['p05']:.1f}", f"{r['grazed_lift']['p95']:.1f}"],
                "ear_only_lift": f"{r['ear_lift']['mean']:.0f}x",
                "graze_at_shot": f"{100 * r['grazed_shot']['mean']:.2f}%",
                "graze_speech_average": f"{100 * r['grazed_avg']['mean']:.2f}%",
                "ear_only_at_shot": f"{100 * r['ear_shot']['mean']:.2f}%",
                "ear_only_speech_average": f"{100 * r['ear_avg']['mean']:.2f}%",
                "graze_speech_average_one_in": f"1 in {one_in(r['grazed_avg']['mean'])}",
                "ear_only_speech_average_one_in": f"1 in {one_in(r['ear_avg']['mean'])}",
                # head-aimed shots at random moments of the speech for an even chance of one ear-only hit
                "shots_for_even_chance_ear_only": int(round(np.log(0.5) / np.log(1 - r["ear_avg"]["mean"]), -1)),
                "shots_for_even_chance_graze": int(round(np.log(0.5) / np.log(1 - r["grazed_avg"]["mean"])))}

    def one_in(p):  # 1/p: whole numbers below 200 (1 in 105), two significant figures above (1 in 990)
        n = 1 / p
        if n < 200:
            return int(round(n))
        k = int(np.floor(np.log10(n))) - 1
        return int(round(n / 10 ** k) * 10 ** k)
    # The rounded figures RESULTS.md and the pages quote, so nobody has to round by hand.
    res["quoted"] = {"wound_corrected": quoted(res["pitch_averaged"]),
                     "video_only": quoted(res["video_only_pitch_averaged"])}
    OUT.write_text(json.dumps(res, indent=1))
    chart()
    for k in ("pitch_averaged", "level_head", "video_only_pitch_averaged"):
        r = res[k]
        print(k, {a: round(b["mean"], 4) if isinstance(b, dict) else b for a, b in r.items()})
