"""Hold the real first bullet's path fixed in the torso frame (top_down_view.json) and ask, over head turn,
nod and tilt, whether it enters the skull (bone) or brain, and how close it comes. Writes
results/path_by_head_angle.json. Uses margin.clearance (rings of rays parallel to the path)."""
import json, sys, time
from pathlib import Path
import numpy as np
from margin import DASH, clearance
from sim3d import Scene

OUT = Path(__file__).resolve().parents[1] / "results" / "path_by_head_angle.json"


def depth_inside(mesh, a, b):
    """Length of the centreline inside the mesh (chord through bone), 0 if it does not enter."""
    L = np.linalg.norm(b - a); d = (b - a) / L
    locs, _, _ = mesh.ray.intersects_location(a[None], d[None])
    ts = np.sort([(p - a) @ d for p in locs if 0 <= (p - a) @ d <= L])
    return float(sum(t1 - t0 for t0, t1 in zip(ts[0::2], ts[1::2])))


if __name__ == "__main__":
    p = json.loads((DASH / "top_down_view.json").read_text())["bullet"]["path_torso_frame_mm"]
    a, b = np.array(p["start"]), np.array(p["end"])
    rels = [float(r) for r in range(-60, 181, 10)]
    pitches, rolls = (-20.0, -10.0, 0.0, 10.0, 20.0), (-15.0, 0.0, 15.0)
    rows, t0 = [], time.time()
    for rel in rels:
        for pitch in pitches:
            for roll in rolls:
                sc = Scene(90.0 - rel, pitch, roll)
                bone, bone_in = clearance(sc.meshes["bone"], a, b, r_max=30.0)
                brain, brain_in = clearance(sc.meshes["brain"], a, b, r_max=30.0)
                rows.append(dict(rel_deg=rel, pitch_deg=pitch, roll_deg=roll, bone_gap_mm=round(bone, 2),
                                 centreline_through_bone=bone_in,
                                 bone_chord_mm=round(depth_inside(sc.meshes["bone"], a, b), 1) if bone_in else 0.0,
                                 brain_gap_mm=round(brain, 2), centreline_through_brain=brain_in))
        print(rel, round(time.time() - t0), flush=True)
        OUT.write_text(json.dumps(dict(
            what="Real first-bullet path held fixed in the torso frame; head turned (rel), nodded (pitch, chin up +) "
                 "and tilted (roll). bone_gap_mm: gap from the bullet's edge (5.7 mm bullet) to bone, negative = "
                 "overlap, -2.85 = centreline enters bone. bone_chord_mm: length of centreline inside bone.",
            path_torso_frame_mm=p, rows=rows), indent=1))
