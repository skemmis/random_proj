"""Shooter's-eye renders of the posed likeness with the outcome of each bullet path painted on.

For each head turn we render the textured bust as Crooks saw it (looking along the line of fire)
and ray-cast one bullet path per pixel through the full model, so the painted zones are exact
for that pose. Results are cached in results/views/ so the figures can be restyled cheaply.
"""

import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from figures_3d import likeness_layers  # noqa: E402
from maps import CODES, grid_codes  # noqa: E402
from render import render  # noqa: E402
from sim3d import Scene, aim_points, fire_direction, plane_basis  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "results" / "views"
SHOOTER_AZ, ELEV = 90.0, 0.8
EXTENT, RES = 150.0, 420  # half-width of the view in mm, pixels


def view_path(rel, pitch=0.0, extent=EXTENT):
    tag = "" if extent == EXTENT else f"_e{extent:.0f}"
    return OUT / f"view_rel{rel:+04.0f}_p{pitch:+03.0f}{tag}.npz"


def make_view(args):
    rel, pitch = args[:2]
    extent = args[2] if len(args) > 2 else EXTENT
    res = RES if extent == EXTENT else int(RES * extent / EXTENT)
    f = view_path(rel, pitch, extent)
    if f.exists():
        return f
    sc = Scene(SHOOTER_AZ - rel, pitch)
    d = fire_direction(SHOOTER_AZ, ELEV)
    right, up = plane_basis(d)
    centre = aim_points(sc, d)["head"] + np.array([0, -25.0 if extent == EXTENT else -150.0, 0])
    img, depth = render(likeness_layers(sc, ear_highlight=False), d, up=(0, 1, 0), res=res,
                        center=centre, extent=extent)
    us = np.linspace(-extent, extent, res)
    codes = grid_codes(sc, d, centre, right, up, us, us[::-1])
    np.savez_compressed(f, img=img, depth=depth, codes=codes, codes_names=np.array(CODES),
                        extent=extent, aim=aim_points(sc, d)["head"] - centre, right=right, up=up)
    print("view", rel, pitch, flush=True)
    return f


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    rels = [float(r) for r in sys.argv[1:]] or [-30, -15, 0, 15, 30, 45, 60, 90]
    with Pool(3) as pool:
        pool.map(make_view, [(r, 0.0) for r in rels], chunksize=1)
