"""How a raised chin at the first shot changes the margin. At the shot's turn (rel 10, as drawn), nod the head
chin-up and measure the gap from the bullet's edge to the skull and to a serious wound (more than 3 mm into the
skin, or any vital structure) two ways:
  fixed_path: the real path from top_down_view.json held fixed in space while the head nods (what would have
              happened had he nodded and the bullet flown the same line);
  wound_path: the path re-centred on the right-ear-only zone at each nod, so it still passes through the top of
              his ear as the real bullet did (what the margin was if he really was chin-up).
Also recounts the at-shot outcomes from the full run's rows with the head level, chin up 10, and pitch-averaged.
Writes results/chin_up_at_shot.json."""
import json
from pathlib import Path
import numpy as np
from analyze import load, video_pose
from maps import CODES, grid_codes
from margin import DASH, LETHAL, clearance
from sim3d import Scene, aim_points, fire_direction, plane_basis

OUT = Path(__file__).resolve().parents[1] / "results" / "chin_up_at_shot.json"
REL, PITCHES = 10.0, (0, 3, 5, 8, 10, 12, 15, 20)


def gaps(sc, a, b):
    r = {k: clearance(sc.meshes[k], a, b) for k in LETHAL}
    g = {k: v[0] for k, v in r.items()}
    return dict(skull_gap_mm=round(g["bone"], 1), serious_wound_gap_mm=round(min(g.values()), 1),
                centreline_through_bone=r["bone"][1])


def at_shot(rows, pitches):
    v = video_pose()
    rels = np.array(sorted({r["rel"] for r in rows if r["roll"] == 0 and -60 <= r["rel"] <= 90 and
                            all(any(q["rel"] == r["rel"] and q["pitch"] == p and q["roll"] == 0 for q in rows)
                                for p in pitches)}))
    val = lambda x, f: np.mean([f(q["head"]) for q in rows if q["rel"] == x and q["roll"] == 0 and q["pitch"] in pitches])
    like = np.array([val(x, lambda h: h["codes"]["ear_only_right"]) for x in rels])
    post = np.exp(-0.5 * ((rels - v["mean"]) / v["sd"]) ** 2) * like
    post /= post.sum()
    out = {k: round(100 * float(post @ np.array([val(x, lambda h: h["buckets"][k]) for x in rels])), 2)
           for k in ("ear_only", "grazed", "killed_or_wounded", "miss")}
    return dict(percent=out, rel_mean_deg=round(float(post @ rels), 1))


if __name__ == "__main__":
    p = json.loads((DASH / "top_down_view.json").read_text())["bullet"]["path_torso_frame_mm"]
    a0, b0 = np.array(p["start"]), np.array(p["end"])
    d = fire_direction(90.0, 0.8)
    right, up = plane_basis(d)
    us = np.arange(-150, 150.01, 1.0)
    rows = []
    for pitch in PITCHES:
        sc = Scene(90.0 - REL, float(pitch), 0.0)
        c0 = aim_points(sc, d)["head"] + np.array([0, -25.0, 0])
        codes = grid_codes(sc, d, c0, right, up, us, us[::-1])
        rr, cc = np.nonzero(codes == CODES.index("ear_only_right"))
        pt = c0 + us[cc].mean() * right + us[::-1][rr].mean() * up
        rows.append(dict(chin_up_deg=pitch, fixed_path=gaps(sc, a0, b0),
                         wound_path=dict(gaps(sc, pt - 170 * d, pt + 150 * d), ear_only_zone_mm2=int(len(rr)))))
        print(rows[-1], flush=True)
    sim = load()
    OUT.write_text(json.dumps(dict(
        what=__doc__, rel_deg=REL, bullet_diameter_mm=5.7, rows=rows,
        at_shot_outcomes=dict(level=at_shot(sim, [0.0]), chin_up_10=at_shot(sim, [10.0]),
                              pitch_averaged_as_quoted=at_shot(sim, [-10.0, 0.0, 10.0, 20.0]))), indent=1))
