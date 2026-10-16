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
    # Per-moment series for the dashboard, so a timeline can be coloured from the same trace as the shares.
    names = {"ear": "ear_only", "graze": "grazed", "kill": "deeper", "miss": "missed", "arm": "arm"}
    mb = json.loads((RES / "margin_by_degree.json").read_text())["by_rel_deg"]  # made by margin_by_degree.py
    deg = lambda r: float(np.round(wrap(float(r["rel_deg"]) + off)))
    sk = json.loads((RES / "skin_by_degree.json").read_text())["by_rel_deg"]  # made by skin_by_degree.py
    three = {"ear": "ear_only", "graze": "serious_wound_or_death", "kill": "serious_wound_or_death",
             "miss": "miss", "arm": "serious_wound_or_death"}
    frames = [[float(r["t_s"]), round(float(r["rel_deg"]) + off, 1), names[oc[deg(r)]]] + mb[str(int(deg(r)))]
              + [sk[str(int(deg(r)))], three[oc[deg(r)]]]
              for r in csv.DictReader(open(B / "video/pose_track.csv"))]
    (B / "assets/dashboard/real_path_by_moment.json").write_text(json.dumps(dict(
        what="What the real first bullet's line would have done at each measured moment of the speech: the trace "
             "behind the quoted shares (results/path_share.json, quoted.real_path_over_speech in speech_luck.json). "
             "Shares are counted over frames with t_s < 0.",
        frames_fields=["t_s: seconds before the first bullet arrived (0 = the shot), one row per measured frame, "
                       "5 a second, with gaps where the camera cut away (video/pose_track.csv)",
                       "rel_deg: head turn with the wound's shift applied (0 = face at the rifle, negative = past it)",
                       "outcome: ear_only, grazed, deeper or missed",
                       "skull_mm: gap from the bullet's edge (5.7 mm across) to the nearest bone; negative = the edge "
                       "cuts that far in; -2.85 = the centreline enters",
                       "serious_wound_mm: the same for the nearest tissue that counts as a serious wound (bone, "
                       "brain, vessel, airway, eye, or deeper than 3 mm under the skin): the old four-outcome line",
                       "skin_mm: gap from the bullet's edge to the skin of his head or neck (ear excluded); since "
                       "2026-10-16 any touch of that skin is a serious wound, so this is the current margin",
                       "outcome3: the three outcomes Sam set on 2026-10-16: ear_only, serious_wound_or_death or miss"],
        by_rel_deg3={str(int(k)): three[v] for k, v in sorted(oc.items())},
        skin_by_rel_deg=sk,
        gap_by_rel_deg_fields=["skull_mm", "serious_wound_mm"],
        gap_by_rel_deg=mb,
        by_rel_deg_fields="outcome (gap_by_rel_deg: the two gaps) at every whole degree of turn from -180 to 180; round a smoothed turn to the "
                          "nearest degree and look it up here to colour frames between the measured ones",
        shift_deg=round(off, 2), frames=frames,
        by_rel_deg={str(int(k)): names[v] for k, v in sorted(oc.items())}), separators=(",", ":")))
    print(out["quoted"], bands)
