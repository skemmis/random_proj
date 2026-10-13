"""How slim was the margin? Distance from the edge of the real bullet (5.7 mm across) to the skull and to the
nearest tissue that counts as killed or seriously wounded, with the bullet path held fixed in the torso frame
(as in the dashboard's top_down_view.json) while the head turns through the hit-map grid."""
import json
from pathlib import Path
import numpy as np
import trimesh
from sim3d import Scene

DASH = Path("/mnt/project-files/butler-shooting/assets/dashboard")
R_BULLET = 2.85
LETHAL = ("brain", "vessel", "bone", "airway", "eye", "deep_soft")
STEP = 0.25


def clearance(mesh, a, b):
    """Positive: gap in mm from the bullet's edge to the mesh. Negative: how deep the bullet's edge reaches into it."""
    L = np.linalg.norm(b - a)
    d = (b - a) / L
    pts = a + np.outer(np.arange(0, L + STEP, STEP), d)
    _, dist, _ = trimesh.proximity.closest_point(mesh, pts)
    locs, _, _ = mesh.ray.intersects_location(a[None], d[None])
    ts = np.sort([(p - a) @ d for p in locs if 0 <= (p - a) @ d <= L])
    if len(ts) < 2:
        return float(dist.min() - R_BULLET)
    s = np.arange(0, L + STEP, STEP)
    inside = np.zeros(len(s), bool)
    for t0, t1 in zip(ts[0::2], ts[1::2]):
        inside |= (s >= t0) & (s <= t1)
    return float(-(dist[inside].max() + R_BULLET)) if inside.any() else float(dist.min() - R_BULLET)


def margins(rel, a, b):
    sc = Scene(90.0 - rel)
    out = {k: clearance(sc.meshes[k], a, b) for k in LETHAL}
    skull = out["bone"]
    worst = min(out, key=out.get)
    return dict(rel_deg=rel, skull_or_spine_mm=round(skull, 2), lethal_mm=round(out[worst], 2),
                nearest_lethal_structure=worst, by_structure_mm={k: round(v, 2) for k, v in out.items()})


if __name__ == "__main__":
    td = json.loads((DASH / "top_down_view.json").read_text())
    p = td["bullet"]["path_torso_frame_mm"]
    a, b = np.array(p["start"]), np.array(p["end"])
    rows = [margins(float(r), a, b) for r in range(-60, 181, 5)]
    real = next(r for r in rows if r["rel_deg"] == td["pose"]["rel_deg"])
    out = dict(
        what="Gap between the edge of the real bullet (5.7 mm across) and his anatomy, with the bullet path from "
             "top_down_view.json held fixed in the torso frame while the head turns.",
        fields=dict(rel_deg="head turn relative to the rifle (0 = face at the rifle, negative = turned past it)",
                    skull_or_spine_mm="gap from the bullet's edge to the nearest bone; negative = how deep the "
                                      "bullet's edge would reach into it",
                    lethal_mm="the same for the nearest tissue that counts as killed or seriously wounded: brain, "
                              "major vessel, bone, airway, eye, or more than 3 mm into the skin (deep_soft)",
                    nearest_lethal_structure="which structure sets lethal_mm",
                    by_structure_mm="the gap to each structure"),
        bullet_path_torso_frame_mm=dict(start=p["start"], end=p["end"]),
        bullet_radius_mm=R_BULLET, real_pose=real, rows=rows)
    (DASH / "margin_by_turn.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(real, indent=1))
    for r in rows:
        print(r["rel_deg"], r["skull_or_spine_mm"], r["lethal_mm"], r["nearest_lethal_structure"])
