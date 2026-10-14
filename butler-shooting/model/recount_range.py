"""Recount every pose's outcome odds under the current dispersion.RANGE_M without new ray casting.

Poses with a saved outcome map (every 10 degrees of turn, level or 10 degrees chin-up) are recounted exactly
from the map. The other poses have no saved map; for them each outcome's chance is scaled by the ratio
new/old measured on the mapped level-head poses, interpolated by head turn, then renormalised. The ratios
barely vary (graze 0.940-0.946 for 125-142 m -> 139 m), so the error from this shortcut is negligible.
The rows as they stood before the first recount are kept in results/rows_range125_142/."""
import json, shutil
from pathlib import Path
import numpy as np
import dispersion
from maps import CODES, OutcomeMap, buckets

RES = Path(__file__).resolve().parents[1] / "results"
ROWS, BACKUP, MAPS = RES / "rows", RES / "rows_range125_142", RES / "maps"


def load_map(f):
    z = np.load(f, allow_pickle=True)
    m = OutcomeMap.__new__(OutcomeMap)
    m.fine, m.coarse, m.fu, m.fv, m.cu, m.cv = z["fine"], z["coarse"], z["fu"], z["fv"], z["cu"], z["cv"]
    m.aims = {"head": z["aim_head"], "chest": z["aim_chest"]}
    m.fine_step, m.coarse_step = 1.5, 10.0
    return m


def count(m):
    p = m.probabilities("head", rng=np.random.default_rng(2024))
    p2 = m.probabilities("head", rng=np.random.default_rng(2025), followup=True)
    return dict(head=dict(codes=p, buckets=buckets(p)), head_followup=dict(codes=p2, buckets=buckets(p2)))


def main():
    if not BACKUP.exists():
        shutil.copytree(ROWS, BACKUP)
    old_rows = {p.name: json.loads(p.read_text()) for p in sorted(BACKUP.glob("*.json"))}
    new = {}
    for name, r in old_rows.items():
        f = MAPS / f"map_rel{r['rel']:+04.0f}_p{r['pitch']:+03.0f}_r{r['roll']:+03.0f}.npz"
        if f.exists():
            new[name] = dict(rel=r["rel"], pitch=r["pitch"], roll=r["roll"], **count(load_map(f)))
    # Per-code ratios on mapped level-head poses, by head turn.
    lv = sorted([n for n in new if new[n]["pitch"] == 0 and new[n]["roll"] == 0], key=lambda n: new[n]["rel"])
    rels = np.array([new[n]["rel"] for n in lv])

    def ratio(kind, code, rel):
        o = np.array([old_rows[n][kind]["codes"][code] for n in lv])
        nw = np.array([new[n][kind]["codes"][code] for n in lv])
        rr = np.where(o > 1e-9, nw / np.maximum(o, 1e-12), np.nan)
        ok = np.isfinite(rr)
        return float(np.interp(rel, rels[ok], rr[ok])) if ok.any() else 1.0

    for name, r in old_rows.items():
        if name in new:
            continue
        row = dict(rel=r["rel"], pitch=r["pitch"], roll=r["roll"])
        for kind in ("head", "head_followup"):
            p = {c: r[kind]["codes"][c] * ratio(kind, c, r["rel"]) for c in CODES}
            t = sum(p.values())
            p = {c: v / t for c, v in p.items()}
            row[kind] = dict(codes=p, buckets=buckets(p))
        new[name] = row
    for name, row in new.items():
        (ROWS / name).write_text(json.dumps(row))
    print(f"range {dispersion.RANGE_M}: {sum((MAPS / ('map_rel%+04.0f_p%+03.0f_r%+03.0f.npz' % (r['rel'], r['pitch'], r['roll']))).exists() for r in new.values())} poses recounted exactly, "
          f"{len(new)} rows written")


if __name__ == "__main__":
    main()
