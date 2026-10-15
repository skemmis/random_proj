"""margin.py's gaps at every whole degree of head turn from -180 to 180, for the per-moment dashboard file
(path_share.py merges them into assets/dashboard/real_path_by_moment.json). Writes results/margin_by_degree.json."""
import json
from multiprocessing import Pool
from pathlib import Path
import numpy as np
from margin import DASH, margins

OUT = Path(__file__).resolve().parents[1] / "results" / "margin_by_degree.json"
P = json.loads((DASH / "top_down_view.json").read_text())["bullet"]["path_torso_frame_mm"]


def one(rel):
    m = margins(float(rel), np.array(P["start"]), np.array(P["end"]))
    return str(int(rel)), [m["skull_or_spine_mm"], m["lethal_mm"]]


if __name__ == "__main__":
    with Pool(3) as pool:
        rows = dict(pool.map(one, range(-180, 181), chunksize=4))
    OUT.write_text(json.dumps(dict(
        what="Gap in mm from the real bullet's edge (5.7 mm across) to the nearest bone and to the nearest tissue "
             "that counts as a serious wound, path held fixed, head level, at each whole degree of turn. Negative = "
             "the bullet's edge cuts that far in; -2.85 = the centreline itself enters.",
        fields=["skull_mm", "serious_wound_mm"], by_rel_deg=rows), indent=0))
    print("rel 10:", rows["10"])
