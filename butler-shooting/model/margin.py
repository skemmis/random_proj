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


def _ring_hits(mesh, a, d, L, r, n_ang=72):
    """Does any ray parallel to the path, at distance r from its centreline, hit the mesh within the segment?"""
    right = np.cross(d, [0, 1.0, 0]); right /= np.linalg.norm(right)
    up = np.cross(right, d)
    ang = np.linspace(0, 2 * np.pi, n_ang, endpoint=False) if r > 0 else np.zeros(1)
    o = a + r * (np.outer(np.cos(ang), right) + np.outer(np.sin(ang), up))
    locs, idx, _ = mesh.ray.intersects_location(o, np.repeat(d[None], len(o), 0), multiple_hits=False)
    if len(locs) == 0:
        return False
    t = np.einsum("ij,j->i", locs - o[idx], d)
    return bool(np.any((t >= 0) & (t <= L)))


def clearance(mesh, a, b, r_max=60.0):
    """Gap in mm from the bullet's edge to the mesh (rays parallel to the path, on rings of growing radius).
    Negative: the bullet's edge overlaps the mesh by that much (the smallest ring that touches it lies inside the
    bullet). Returns (gap, passes_through) where passes_through means the centreline itself enters the mesh."""
    L = np.linalg.norm(b - a); d = (b - a) / L
    if _ring_hits(mesh, a, d, L, 0.0):
        return -R_BULLET, True
    lo, hi = 0.0, None
    for r in np.arange(0.25, r_max + 0.25, 0.25):
        if _ring_hits(mesh, a, d, L, r):
            hi = r
            break
        lo = r
    if hi is None:
        return float(r_max - R_BULLET), False
    for _ in range(5):  # refine to ~0.01 mm
        m = 0.5 * (lo + hi)
        lo, hi = (lo, m) if _ring_hits(mesh, a, d, L, m) else (m, hi)
    return float(hi - R_BULLET), False


def margins(rel, a, b):
    sc = Scene(90.0 - rel)
    res = {k: clearance(sc.meshes[k], a, b) for k in LETHAL}
    out = {k: v[0] for k, v in res.items()}
    worst = min(out, key=out.get)
    return dict(rel_deg=rel, skull_or_spine_mm=round(out["bone"], 2), lethal_mm=round(out[worst], 2),
                nearest_lethal_structure=worst, centreline_enters=[k for k, v in res.items() if v[1]],
                by_structure_mm={k: round(v, 2) for k, v in out.items()})


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
                    centreline_enters="structures the bullet's centreline itself passes into; their gap is "
                                      "reported as -2.85 (the whole bullet radius), meaning 'at least that deep'",
                    by_structure_mm="the gap to each structure; 57.15 means nothing within 60 mm of the centreline"),
        bullet_path_torso_frame_mm=dict(start=p["start"], end=p["end"]),
        bullet_radius_mm=R_BULLET, real_pose=real, rows=rows)
    (DASH / "margin_by_turn.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(real, indent=1))
    for r in rows:
        print(r["centreline_enters"], r["rel_deg"], r["skull_or_spine_mm"], r["lethal_mm"], r["nearest_lethal_structure"])
