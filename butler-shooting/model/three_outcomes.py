"""Three outcomes, as Sam decided on 2026-10-16: Ear only, Serious wound or death, Miss. Skin grazes (the outer 3 mm
of skin away from the ear) and arm-only hits join Serious wound or death. As a marked variant, skin grazes count as misses
instead. Arithmetic on the full run's rows and the existing track weighting (same seed and draws as
speech_luck.py); nothing is re-simulated. Writes results/three_outcomes.json."""
import csv
import json
from pathlib import Path
import numpy as np
import speech_luck as sl
from path_share import whole_percents

RES = Path(__file__).resolve().parents[1] / "results"
B = Path("/mnt/project-files/butler-shooting")


def speech_average(n=4000, seed=7):
    """Speech-average chance of each outcome, pitch-averaged, track shifted by the wound-weighted offset."""
    keys = {"ear": lambda r: r["head"]["buckets"]["ear_only"], "miss": lambda r: r["head"]["buckets"]["miss"],
            "grazed": lambda r: r["head"]["buckets"]["grazed"]}
    C = {k: sl.by_rel_pitch_avg(sl.rows, f, lo=-60, hi=180) for k, f in keys.items()}
    C["ear_right"] = sl.curves(False)["ear_right"]
    f = {k: (lambda x, k=k: np.interp(x, *C[k])) for k in C}
    t, rel = [], []
    for r in csv.DictReader(sl.TRACK.open()):
        if r["rel_deg"]:
            t.append(float(r["t_s"])); rel.append(float(r["rel_deg"]))
    t, rel = np.array(t), np.array(rel)
    shot = json.loads((B / "video/pose_handoff.json").read_text())["pose_relative_to_rifle"]["yaw"]["mean"]
    rng = np.random.default_rng(seed)
    sd = float(np.median([float(r["rel_sd_deg"]) for r in csv.DictReader(sl.TRACK.open()) if r["rel_sd_deg"]]))
    e = rng.normal(0, sd, 40 * n)
    w = f["ear_right"](shot + e)
    e = rng.choice(e, n, p=w / w.sum())
    x = rel[t < 0][None, :] + e[:, None]
    return {k: float(f[k](x).mean()) for k in ("ear", "miss", "grazed")}


def three(ear, grazed, miss, as_miss=False):
    skin = grazed - ear
    m = miss + (skin if as_miss else 0.0)
    return {"ear_only": ear, "serious_wound_or_death": 1.0 - ear - m, "miss": m}


def one_in(p):
    n = 1 / p
    return f"1 in {int(round(n))}" if n < 200 else f"1 in {int(float(f'{n:.2g}'))}"


if __name__ == "__main__":
    S = json.loads((RES / "summary.json").read_text())
    at = S["video_and_wound"]["given_estimated_pose"]
    crowd = S["facing_crowd_rel90"]
    sp = speech_average()
    fa = json.loads((RES / "face_areas.json").read_text())
    ps = json.loads((RES / "path_share.json").read_text())["share"]
    out = {"what": __doc__}
    for name, am in (("default", False), ("skin_graze_as_miss", True)):
        A = three(at["ear_only"], at["grazed"], at["miss"], am)
        Sp = three(sp["ear"], sp["grazed"], sp["miss"], am)
        Cr = three(crowd["ear_only"], crowd["grazed"], crowd["miss"], am)
        ca, ha = fa["circle_share"], fa["head_alone_share"]
        circ = {"ear_only": ca["ear_only"], "serious_wound_or_death": ca["serious"] + ca["arm"] + (0 if am else ca["skin_graze"]),
                "miss": ca["miss"] + (ca["skin_graze"] if am else 0)}
        head = {"ear_only": ha["ear_only"], "serious_wound_or_death": ha["serious"] + (0 if am else ha["skin_graze"]),
                "miss": ha["skin_graze"] if am else 0.0}
        path = {"ear_only": ps["ear"], "serious_wound_or_death": ps["kill"] + ps["arm"] + (0 if am else ps["graze"]),
                "miss": ps["miss"] + (ps["graze"] if am else 0)}
        out[name] = dict(at_his_turn=A, random_moment=Sp, facing_crowd=Cr, area_circle_19cm=circ,
                         area_head_alone=head, real_path_over_speech=path)
    d = out["default"]
    pc = lambda x, nd=1: f"{100 * x:.{nd}f}%"
    out["quoted"] = {
        "outcome_names": ["Ear only", "Serious wound or death", "Miss"],
        # the real bullet at his turn (rel 10): gap from its edge to the skull, and to the skin of his scalp, which
        # under three outcomes is the line to a serious wound (model/margin.py clearance; skin_by_degree.py)
        "margin_at_his_turn_mm": {"skull": 6.1, "skin": 0.7},
        "at_his_turn": {"ear_only": pc(d["at_his_turn"]["ear_only"], 2), "serious_wound_or_death": pc(d["at_his_turn"]["serious_wound_or_death"]),
                        "miss": pc(d["at_his_turn"]["miss"]), "ear_only_one_in": "about 1 in 135",
                        "shots_for_even_chance_ear_only": int(round(np.log(0.5) / np.log(1 - d["at_his_turn"]["ear_only"])))},
        "random_moment": {"ear_only": pc(d["random_moment"]["ear_only"], 2), "ear_only_one_in": one_in(d["random_moment"]["ear_only"]),
                          "serious_wound_or_death": pc(d["random_moment"]["serious_wound_or_death"]), "miss": pc(d["random_moment"]["miss"])},
        "facing_crowd": {k: pc(v) for k, v in d["facing_crowd"].items()},
        "area_circle_19cm": {k: pc(v) for k, v in d["area_circle_19cm"].items()},
        "area_head_alone": {k: pc(v) for k, v in d["area_head_alone"].items()},
        # rounded from the four-part whole percents (20 / 14 + 58 / 8) so the parts and the sum agree
        "real_path_over_speech": (lambda w: {"ear_only": f"{w['ear']}%", "serious_wound_or_death": f"{w['graze'] + w['kill']}%",
                                             "miss": f"{w['miss']}%"})(whole_percents({k: ps[k] for k in ("ear", "graze", "kill", "miss")})),
    }
    (RES / "three_outcomes.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out["quoted"], indent=1))
    print(json.dumps({k: {kk: {a: round(100 * b, 2) for a, b in vv.items()} for kk, vv in out[k].items()} for k in ("default", "skin_graze_as_miss")}, indent=1))
