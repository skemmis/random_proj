"""Export the fitted head meshes for the browser skull-fitting tool.

One-command refresh after rebuilding assets/head_model/:

    python model/export_fit_tool.py [--out DIR]

Reads (never writes) assets/head_model/:
  skin_head.ply + skin_head_ear_flags.npy   bust skin, ears flagged 1/2
  skull_cranium.ply                         decimated to ~25k faces
  mandible.ply                              kept as is (small)
  teeth.ply                                 split into upper / lower by connected component
                                            (lower = component centroid below y = -42 mm), decimated
  eyeball_left.ply / eyeball_right.ply      decimated, context only

Writes DIR/fit_data.json (default: the fit_tool scratch folder next to index.html):
  {"version", "generated_utc", "frame", "sources": {file: mtime}, "meshes": {name: {
      "positions": base64 float32 xyz, "indices": base64 uint16|uint32, "index_bits": 16|32,
      "ear_flags": base64 uint8 (skin only)}}}

Frame: mm, x = subject's left, y = up, z = forward (face), origin = mid-porion.
The page (index.html) fetches fit_data.json, so republishing both files is the whole refresh.
"""

import argparse
import base64
import datetime as dt
import json
from pathlib import Path

import fast_simplification
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "assets" / "head_model"
DEFAULT_OUT = Path(
    "/tmp/claude-0/-home-user-random-proj/c0d0a617-bcbd-51c7-af85-bd79f1cb1b2e/scratchpad/fit_tool"
)

CRANIUM_FACES = 25000
TEETH_FACES_EACH = 4000
EYE_FACES = 1200
LOWER_TEETH_Y = -42.0  # mm; upper crowns sit above this, lower crowns below


def load(name):
    m = trimesh.load(SRC / f"{name}.ply", process=False)
    return np.asarray(m.vertices, np.float64), np.asarray(m.faces, np.int64)


def decimate(v, f, target_faces):
    if len(f) <= target_faces:
        return v, f
    reduction = 1.0 - target_faces / len(f)
    v2, f2 = fast_simplification.simplify(v.astype(np.float32), f.astype(np.int32), target_reduction=reduction)
    return np.asarray(v2, np.float64), np.asarray(f2, np.int64)


def compact(v, f):
    used = np.unique(f)
    remap = -np.ones(len(v), np.int64)
    remap[used] = np.arange(len(used))
    return v[used], remap[f]


def b64(a):
    return base64.b64encode(np.ascontiguousarray(a).tobytes()).decode("ascii")


def pack(v, f, **extra):
    bits = 16 if len(v) < 65536 else 32
    out = {
        "positions": b64(v.astype("<f4")),
        "indices": b64(f.astype("<u2" if bits == 16 else "<u4")),
        "index_bits": bits,
        "n_vertices": int(len(v)),
        "n_faces": int(len(f)),
    }
    for k, a in extra.items():
        out[k] = b64(a)
    return out


def split_teeth(v, f):
    """Return (upper_faces, lower_faces) of teeth.ply by connected component height."""
    mesh = trimesh.Trimesh(v, f, process=False)
    mesh.merge_vertices()  # PLY seams would otherwise split teeth into slivers
    labels = trimesh.graph.connected_component_labels(mesh.face_adjacency, node_count=len(mesh.faces))
    centroids = mesh.triangles_center
    lower_face = np.zeros(len(mesh.faces), bool)
    for lab in np.unique(labels):
        sel = labels == lab
        if centroids[sel, 1].mean() < LOWER_TEETH_Y:
            lower_face |= sel
    mv, mf = np.asarray(mesh.vertices), np.asarray(mesh.faces)
    return compact(mv, mf[~lower_face]), compact(mv, mf[lower_face])


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    meshes = {}
    sources = {}

    def note(name):
        p = SRC / name
        sources[name] = dt.datetime.fromtimestamp(p.stat().st_mtime, dt.timezone.utc).isoformat(timespec="seconds")

    v, f = load("skin_head")
    flags = np.load(SRC / "skin_head_ear_flags.npy").astype(np.uint8)
    assert len(flags) == len(v), "ear flags do not match skin_head vertices"
    meshes["skin"] = pack(v, f, ear_flags=flags)
    note("skin_head.ply"); note("skin_head_ear_flags.npy")

    v, f = load("skull_cranium")
    meshes["cranium"] = pack(*compact(*decimate(v, f, CRANIUM_FACES)))
    note("skull_cranium.ply")

    v, f = load("mandible")
    meshes["mandible"] = pack(v, f)
    note("mandible.ply")

    v, f = load("teeth")
    (uv, uf), (lv, lf) = split_teeth(v, f)
    meshes["teeth_upper"] = pack(*compact(*decimate(uv, uf, TEETH_FACES_EACH)))
    meshes["teeth_lower"] = pack(*compact(*decimate(lv, lf, TEETH_FACES_EACH)))
    note("teeth.ply")

    for side in ("left", "right"):
        name = f"eyeball_{side}"
        if (SRC / f"{name}.ply").exists():
            v, f = load(name)
            meshes[f"eye_{side}"] = pack(*compact(*decimate(v, f, EYE_FACES)))
            note(f"{name}.ply")

    data = {
        "version": 1,
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "frame": "mm; x = subject's left, y = up, z = forward (face); origin = mid-porion",
        "sources": sources,
        "meshes": meshes,
    }
    out = args.out / "fit_data.json"
    out.write_text(json.dumps(data, separators=(",", ":")))
    print(f"wrote {out} ({out.stat().st_size / 1e6:.2f} MB)")
    for k, m in meshes.items():
        print(f"  {k:12s} {m['n_vertices']:7d} v {m['n_faces']:7d} f")
    if not (args.out / "index.html").exists():
        print("note: index.html not found next to fit_data.json")


if __name__ == "__main__":
    main()
