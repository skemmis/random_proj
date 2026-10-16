"""Gap in mm from the real bullet's edge to the skin of his head or neck (scalp, face, neck; the ear excluded),
path held fixed, head level, at each whole degree of turn. Since Sam cut the skin-graze outcome (2026-10-16), any
touch of that skin is a wound, so this is the margin to "Wound or death". Writes results/skin_by_degree.json."""
import json
from multiprocessing import Pool
from pathlib import Path
import numpy as np
from margin import DASH, clearance
from sim3d import Scene

OUT = Path(__file__).resolve().parents[1] / "results" / "skin_by_degree.json"
P = json.loads((DASH / "top_down_view.json").read_text())["bullet"]["path_torso_frame_mm"]


def one(rel):
    sc = Scene(90.0 - float(rel))
    a, b = np.array(P["start"]), np.array(P["end"])
    return str(int(rel)), round(min(clearance(sc.meshes[k], a, b)[0] for k in ("scalp", "face", "neck")), 2)


if __name__ == "__main__":
    with Pool(3) as pool:
        rows = dict(pool.map(one, range(-180, 181), chunksize=4))
    OUT.write_text(json.dumps(dict(what=__doc__.split("Writes")[0].strip(), by_rel_deg=rows), indent=0))
    print("rel 10:", rows["10"])
