"""Sweep head pose and record outcome probabilities for head and chest aim.

Writes results/sweep.json (one row per pose) and results/maps/*.npz for selected poses.
Pose is described by rel = shooter_az - head_yaw (0 = face toward the shooter, 90 = right ear
toward the shooter), plus head pitch (chin up +) and roll (top of head toward his left -).
"""

import json
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from maps import CODES, OutcomeMap, buckets  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "results"
SHOOTER_AZ = 90.0


def row_path(pose):
    rel, pitch, roll = pose
    return OUT / "rows" / f"rel{rel:+04.0f}_p{pitch:+03.0f}_r{roll:+03.0f}.json"


def run(pose):
    rel, pitch, roll = pose
    if row_path(pose).exists():
        return json.loads(row_path(pose).read_text())
    m = OutcomeMap(shooter_az=SHOOTER_AZ, head_yaw=SHOOTER_AZ - rel, head_pitch=pitch, head_roll=roll)
    row = dict(rel=rel, pitch=pitch, roll=roll)
    for aim in ("head",):  # Sam, 2026-10-13: analyse a head-aimed shot only
        rng = np.random.default_rng(2024)
        p = m.probabilities(aim, n_eng=20_000, rng=rng)
        row[aim] = dict(codes=p, buckets=buckets(p))
        rng = np.random.default_rng(2025)
        p2 = m.probabilities(aim, n_eng=20_000, rng=rng, followup=True)
        row[aim + "_followup"] = dict(codes=p2, buckets=buckets(p2))
    if pitch in (0.0, 10.0) and roll == 0.0 and rel % 10 == 0:
        (OUT / "maps").mkdir(parents=True, exist_ok=True)
        np.savez_compressed(OUT / "maps" / f"map_rel{rel:+04.0f}_p{pitch:+03.0f}_r{roll:+03.0f}.npz",
                            fine=m.fine, coarse=m.coarse, fu=m.fu, fv=m.fv, cu=m.cu, cv=m.cv,
                            aim_head=m.aims["head"], aim_chest=m.aims["chest"], codes=np.array(CODES))
    row_path(pose).write_text(json.dumps(row))
    print(f"rel {rel:+4.0f} pitch {pitch:+3.0f} roll {roll:+3.0f}: grazed {row['head']['buckets']['grazed']:.3%}, ear-only {row['head']['buckets']['ear_only']:.3%}",
          flush=True)
    return row


def main():
    (OUT / "rows").mkdir(parents=True, exist_ok=True)
    # Each pose is saved as soon as it finishes, so a crashed worker loses one pose, not the run.
    # Three workers: four ran out of memory (each holds the 600k-face hair mesh and its BVH).
    poses = [(float(r), 0.0, 0.0) for r in range(-60, 181, 5)]
    for pitch in (-10.0, 10.0, 20.0):
        poses += [(float(r), pitch, 0.0) for r in range(-40, 71, 5)]
    for roll in (-10.0, -20.0, 10.0):
        poses += [(float(r), 0.0, roll) for r in range(-40, 71, 5)]
        poses += [(float(r), 10.0, roll) for r in range(-40, 71, 5)]
    with Pool(3, maxtasksperchild=20) as pool:
        rows = pool.map(run, poses, chunksize=1)
    (OUT / "sweep.json").write_text(json.dumps(rows, indent=0))


if __name__ == "__main__":
    main()
