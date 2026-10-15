"""Surface area by outcome, as the rifle saw his head at the shot (face 10 degrees short of the rifle, head level).
Each 0.5 mm cell of the shooter's-eye view is coded by what a bullet whose centre passes there would do (the same
5.7 mm bullet and outcome rules as the simulation), so areas are where the bullet's centre could pass. Shares are
given two ways: of the head alone (every cell that touches him above the shoulders), and of a circle around the
aim point that holds half of all simulated head-aimed shots (cells there that touch nothing are misses; torso
counts as a serious wound, as in the simulation). Pure geometry: no shots are simulated except to size the circle.
Writes results/face_areas.json and assets/dashboard/face_map_rel10.png (codes image) + face_map_rel10.json."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
from dispersion import PRIORS, moa_to_cm, sample_engagements
from maps import CODES, grid_codes
from sim3d import Scene, aim_points, fire_direction, plane_basis

REL, STEP = 10.0, 0.5
RES = Path(__file__).resolve().parents[1] / "results"
DASH = Path("/mnt/project-files/butler-shooting/assets/dashboard")
GROUP = {"miss": "miss", "miss_hair": "miss", "ear_only_right": "ear_only", "ear_only_left": "ear_only",
         "graze_skin": "skin_graze", "arm": "arm"}  # everything else: serious wound or death


def half_radius_mm(n=200_000, seed=2024):
    rng = np.random.default_rng(seed)
    e = sample_engagements(n, rng, PRIORS)
    x = e["bx"] + rng.normal(0, 1, n) * e["sx"]
    y = e["by"] + rng.normal(0, 1, n) * e["sy"]
    return float(np.median(np.hypot(moa_to_cm(x, e["range_m"]), moa_to_cm(y, e["range_m"]))) * 10)


if __name__ == "__main__":
    R = half_radius_mm()
    sc = Scene(90.0 - REL)
    d = fire_direction(90.0, 0.8)
    right, up = plane_basis(d)
    aim = aim_points(sc, d)["head"]
    half = np.ceil(R / 10) * 10
    us = np.arange(-half, half + 1e-9, STEP)
    codes = grid_codes(sc, d, aim, right, up, us, us[::-1])
    names = np.array(CODES)[codes]
    group = np.vectorize(lambda c: GROUP.get(c, "serious"))(names)
    U, V = np.meshgrid(us, us[::-1])
    inside = np.hypot(U, V) <= R
    cell = STEP * STEP
    # The head alone: every cell that touches him, minus torso and arms.
    head = (group != "miss") & (group != "arm") & (names != "torso")
    keys = ("ear_only", "skin_graze", "serious", "miss")
    head_mm2 = {k: float((head & (group == k)).sum() * cell) for k in keys[:3]}
    circ = {k: float((inside & (group == k)).sum() * cell) for k in keys}
    circ["arm"] = float((inside & (group == "arm")).sum() * cell)
    ht, ct = sum(head_mm2.values()), float(inside.sum() * cell)
    out = dict(
        what=__doc__, rel_deg=REL, cell_mm=STEP, circle_radius_mm=round(R, 1),
        head_alone_mm2={k: round(v) for k, v in head_mm2.items()},
        head_alone_share={k: round(v / ht, 4) for k, v in head_mm2.items()},
        circle_mm2={k: round(v) for k, v in circ.items()},
        circle_share={k: round(v / ct, 4) for k, v in circ.items()})
    out["quoted"] = {
        "ear_share_of_head": f"{100 * out['head_alone_share']['ear_only']:.1f}%",
        "graze_share_of_head": f"{100 * out['head_alone_share']['skin_graze']:.1f}%",
        "serious_share_of_head": f"{100 * out['head_alone_share']['serious']:.1f}%",
        "right_ear_share_of_head": f"{100 * float((head & (names == 'ear_only_right')).sum() * cell) / ht:.1f}%",
        "ear_share_of_circle": f"{100 * out['circle_share']['ear_only']:.1f}%",
        "graze_share_of_circle": f"{100 * out['circle_share']['skin_graze']:.1f}%",
        "serious_share_of_circle": f"{100 * out['circle_share']['serious']:.1f}%",
        "miss_share_of_circle": f"{100 * out['circle_share']['miss']:.1f}%",
        "circle_radius_cm": round(R / 10),
    }
    (RES / "face_areas.json").write_text(json.dumps(out, indent=1))
    Image.fromarray(codes.astype(np.uint8), "L").save(DASH / "face_map_rel10.png", optimize=True)
    (DASH / "face_map_rel10.json").write_text(json.dumps(dict(
        what="Shooter's-eye outcome codes at the shot (face 10 degrees short of the rifle, head level), one pixel per "
             "0.5 mm, centred on the aim point (middle of the skull); u = the shooter's right, v = up. Pixel value = "
             "index into codes. Areas and shares: results/face_areas.json.",
        codes=CODES, mm_per_px=STEP, half_width_mm=float(half), circle_radius_mm=round(R, 1),
        groups={c: GROUP.get(c, "serious") for c in CODES}), indent=1))
    print(json.dumps({k: out[k] for k in ("circle_radius_mm", "head_alone_mm2", "head_alone_share", "circle_share", "quoted")}, indent=1))
