"""What the real first bullet's path would have done at each moment of the speech. The path from
top_down_view.json is held fixed in the torso frame; at every 1 degree of head turn (level head) we trace the
bullet (centre plus six rays on its rim) and classify it: ear only, skin graze, deeper (killed or seriously
wounded), or miss. Then we read the turn at every measured frame before the shot (video/pose_track.csv, with the
wound's 1-degree shift from speech_luck.json) and count shares. The per-degree outcomes are cached in
results/path_outcome_by_rel.json (delete it to retrace, about 15 minutes). Writes results/path_share.json."""
import csv
import json
from pathlib import Path
import numpy as np
from sim3d import BULLET_RADIUS_MM, Scene, classify, plane_basis

B = Path("/mnt/project-files/butler-shooting")
RES = Path(__file__).resolve().parents[1] / "results"
CACHE = RES / "path_outcome_by_rel.json"


def trace_all():
    p = json.loads((B / "assets/dashboard/top_down_view.json").read_text())["bullet"]["path_torso_frame_mm"]
    a, d = np.array(p["start"]), np.array(p["direction"])
    d /= np.linalg.norm(d)
    right, up = plane_basis(d)
    ang = np.linspace(0, 2 * np.pi, 7)[:-1]
    offs = [np.zeros(3)] + [BULLET_RADIUS_MM * (np.cos(t) * right + np.sin(t) * up) for t in ang]

    def outcome(rel):
        sc = Scene(90.0 - rel)
        h = {g: np.array([v.any()]) for g, v in sc.hits(np.array([a - d * 2000 + o for o in offs]),
                                                        np.tile(d, (7, 1))).items()}
        lab = classify(h)[0][0]
        if lab == "grazed":
            return "graze" if (h["scalp"] | h["face"] | h["neck"])[0] else "ear"
        return {"miss": "miss", "arm": "arm"}.get(lab, "kill")

    return {str(r): outcome(r) for r in np.arange(-180, 181, 1.0)}


def whole_percents(x):
    """Round shares to whole percents that add to 100 (largest remainder)."""
    raw = {k: 100 * v for k, v in x.items()}
    out = {k: int(np.floor(v)) for k, v in raw.items()}
    for k in sorted(raw, key=lambda k: raw[k] - out[k], reverse=True)[:100 - sum(out.values())]:
        out[k] += 1
    return out


if __name__ == "__main__":
    if not CACHE.exists():
        CACHE.write_text(json.dumps(trace_all()))
    oc = {float(k): v for k, v in json.loads(CACHE.read_text()).items()}
    off = json.loads((RES / "speech_luck.json").read_text())["pitch_averaged"]["offset_posterior_mean"]
    wrap = lambda x: (x + 180) % 360 - 180
    pre = [oc[float(np.round(wrap(float(r["rel_deg"]) + off)))] for r in csv.DictReader(open(B / "video/pose_track.csv"))
           if float(r["t_s"]) < 0]
    share = {k: pre.count(k) / len(pre) for k in ("ear", "graze", "kill", "miss", "arm")}
    bands, prev = [], None
    for r in sorted(oc):
        if oc[r] != prev:
            bands.append([r, oc[r]])
            prev = oc[r]
    out = dict(what=__doc__, frames=len(pre), offset_deg=round(off, 2), share=share,
               quoted={k: f"{v}%" for k, v in whole_percents(
                   {"ear_only": share["ear"], "graze": share["graze"], "deeper": share["kill"], "miss": share["miss"]}).items()},
               outcome_bands_start_deg=bands)
    (RES / "path_share.json").write_text(json.dumps(out, indent=1))
    print(out["quoted"], bands)
