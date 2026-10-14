"""Export the model's pieces for the interactive dashboard the video thread is building.

    python model/export_dashboard.py [--out DIR]

Writes (default /mnt/project-files/butler-shooting/assets/dashboard/):
  head_model.glb            named nodes: skin (textured), ear_right, ear_left, hair, suit,
                            skull, jaw_teeth, spine, brain, vessels, airway, eyes. Neutral pose,
                            head frame (see README.md).
  hitmaps/                  per head turn: codes_rel+NNN.png (8-bit, pixel value = outcome code)
                            and overlay_rel+NNN.png (RGBA colours), plus hitmaps/index.json.
  outcomes_by_turn.json     chance of each outcome for one head-aimed shot, by head turn.
  dispersion.json           the shot-spread model and its sources.
  charts/                   the data behind every figure.
  README.md                 what each file is, and the frame conventions.
"""

import argparse
import datetime as dt
import json
import shutil
import sys
from pathlib import Path

import fast_simplification
import numpy as np
import trimesh
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from dispersion import PRIORS, RANGE_M  # noqa: E402
from maps import BUCKET, CODES  # noqa: E402
from sim3d import GRAZE_DEPTH_MM, GROUPS, HEAD_PIVOT, fire_direction  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
HM = ROOT / "assets" / "head_model"
RES = ROOT / "results"
DEFAULT_OUT = Path("/mnt/project-files/butler-shooting/assets/dashboard")

COLOURS = {  # RGBA for the overlay PNGs; matches the article figures
    "miss": (0, 0, 0, 0), "miss_hair": (0, 0, 0, 0),
    "ear_only_right": (42, 120, 214, 200), "ear_only_left": (42, 120, 214, 200),
    "graze_skin": (27, 175, 122, 200), "arm": (154, 152, 144, 160),
    "brain": (179, 64, 106, 170), "vessel": (208, 49, 45, 170), "bone": (201, 195, 179, 170),
    "airway": (127, 178, 201, 170), "eye": (60, 60, 60, 170), "torso": (235, 104, 52, 120),
    "deep_soft": (235, 154, 112, 170),
}


def decimate(m, faces):
    if len(m.faces) <= faces:
        return m
    v, f = fast_simplification.simplify(m.vertices.astype(np.float32), m.faces.astype(np.int32),
                                        target_reduction=1 - faces / len(m.faces))
    return trimesh.Trimesh(v, f, process=False)


def load(names):
    return trimesh.util.concatenate([trimesh.load(HM / f"{n}.ply", process=False) for n in names])


def material(rgb, alpha=1.0):
    return trimesh.visual.material.PBRMaterial(baseColorFactor=[*rgb, alpha], metallicFactor=0.0,
                                               roughnessFactor=0.8, doubleSided=True)


def export_glb(out):
    skin = trimesh.load(HM / "skin_head.ply", process=False)
    flags = np.load(HM / "skin_head_ear_flags.npy")
    fflag = flags[skin.faces].max(axis=1)
    uv = np.load(HM / "skin_head_uv.npy")
    tex = Image.open(HM / "skin_head_texture.png").convert("RGB")
    tex.thumbnail((1024, 1024))
    scene = trimesh.Scene()

    def textured(sub_faces, name):
        m = skin.submesh([sub_faces], append=True)
        # submesh keeps vertex order per face; rebuild UVs through the original vertex ids
        vid = np.unique(skin.faces[sub_faces])
        remap = np.full(len(skin.vertices), -1)
        remap[vid] = np.arange(len(vid))
        m = trimesh.Trimesh(skin.vertices[vid], remap[skin.faces[sub_faces]], process=False)
        m.visual = trimesh.visual.TextureVisuals(uv=uv[vid], image=tex)
        scene.add_geometry(m, node_name=name, geom_name=name)

    textured(np.where(fflag == 0)[0], "skin")
    textured(np.where(fflag == 2)[0], "ear_right")
    textured(np.where(fflag == 1)[0], "ear_left")
    suit = trimesh.load(HM / "suit.ply", process=False)
    suit.visual = trimesh.visual.TextureVisuals(uv=np.load(HM / "suit_uv.npy"),
                                                image=Image.open(HM / "suit_texture.png").convert("RGB"))
    scene.add_geometry(suit, node_name="suit", geom_name="suit")
    parts = {
        "skull": (["skull_cranium"], 30000, (0.92, 0.89, 0.80)),
        "jaw_teeth": (["mandible", "teeth"], 12000, (0.92, 0.89, 0.80)),
        "spine": ([f"vertebra_C{i}" for i in range(1, 8)] + ["cervical_discs", "hyoid"], 15000, (0.85, 0.82, 0.74)),
        "brain": (GROUPS["brain"], 25000, (0.86, 0.50, 0.60)),
        "vessels": (GROUPS["vessel"], 12000, (0.82, 0.12, 0.14)),
        "airway": (GROUPS["airway"], 6000, (0.45, 0.70, 0.80)),
        "eyes": (GROUPS["eye"], 3000, (0.95, 0.95, 0.95)),
    }
    info = {}
    for name, (files, nf, rgb) in parts.items():
        m = decimate(load(files), nf)
        m.visual = trimesh.visual.TextureVisuals(material=material(rgb))
        scene.add_geometry(m, node_name=name, geom_name=name)
        info[name] = len(m.faces)
    (out / "head_model.glb").write_bytes(scene.export(file_type="glb"))
    # Hair is ~600k faces of thin cards that don't decimate; keep a random 12% of the cards.
    hair = trimesh.load(HM / "hair.ply", process=False)
    keep = np.random.default_rng(0).random(len(hair.faces)) < 0.12
    hair = trimesh.Trimesh(hair.vertices, hair.faces[keep], process=False)
    hair.remove_unreferenced_vertices()
    hair.visual = trimesh.visual.TextureVisuals(material=material((0.97, 0.86, 0.52)))
    hs = trimesh.Scene()
    hs.add_geometry(hair, node_name="hair", geom_name="hair")
    (out / "hair.glb").write_bytes(hs.export(file_type="glb"))
    info["hair (hair.glb)"] = len(hair.faces)
    return info


def export_hitmaps(out):
    d = out / "hitmaps"
    d.mkdir(parents=True, exist_ok=True)
    index = []
    for f in sorted((RES / "views").glob("view_rel*_p+00.npz")):
        z = np.load(f, allow_pickle=True)
        names = list(z["codes_names"])
        assert names == CODES, "hit maps were made with older outcome codes; re-run views.py"
        rel = float(f.name[8:12])
        tag = f"rel{rel:+04.0f}"
        codes = z["codes"].astype(np.uint8)
        Image.fromarray(codes).save(d / f"codes_{tag}.png")
        rgba = np.array([COLOURS[c] for c in CODES], np.uint8)[codes]
        Image.fromarray(rgba, "RGBA").save(d / f"overlay_{tag}.png")
        img = (np.clip(z["img"], 0, 1) * 255).astype(np.uint8)
        Image.fromarray(img).save(d / f"render_{tag}.png")
        E = float(z["extent"])
        index.append(dict(rel_deg=rel, pitch_deg=0.0, codes=f"codes_{tag}.png", overlay=f"overlay_{tag}.png",
                          render=f"render_{tag}.png", half_width_mm=E, pixels=int(codes.shape[0]),
                          aim_point_uv_mm=[float(z["aim"] @ z["right"]), float(z["aim"] @ z["up"])]))
    meta = dict(
        what="Shooter's-eye outcome maps. Each pixel is one bullet path along the line of fire; its value "
             "is the index into `codes` of what that bullet would do.",
        codes=CODES, bucket_of_code={c: BUCKET[c] for c in CODES},
        image_plane="Orthographic view along the line of fire. Pixel column 0 is the shooter's left edge "
                    "(u = -half_width), row 0 is the top (v = +half_width). u points to the shooter's right, "
                    "v up. The image centre is 25 mm below the centre of the skull.",
        graze_depth_mm=GRAZE_DEPTH_MM, maps=index)
    (d / "index.json").write_text(json.dumps(meta, indent=1))
    return len(index)


def export_outcomes(out):
    """Outcome chances by head turn. Uses the 4 mm sweep when it has run, else the first sweep
    (ear-only numbers are identical under both rules; graze numbers need the new sweep)."""
    rows_dir = RES / "rows"
    rows = [json.loads(p.read_text()) for p in sorted(rows_dir.glob("*.json"))] if rows_dir.exists() else []
    source = f"{GRAZE_DEPTH_MM:.0f} mm graze rule, head aim (current)"
    if not rows:
        rows = json.loads((RES / "sweep_v1.json").read_text())
        source = ("PROVISIONAL: first sweep, before the 4 mm graze rule. Only ear_only_right/ear_only_left "
                  "and their sum are valid under the new rule; other columns use the old categories.")
    table = []
    for r in rows:
        c = r["head"]["codes"]
        table.append(dict(rel_deg=r["rel"], pitch_deg=r["pitch"], roll_deg=r["roll"], codes=c,
                          buckets=r["head"]["buckets"]))
    flat = sorted([t for t in table if t["pitch_deg"] == 0 and t["roll_deg"] == 0], key=lambda t: t["rel_deg"])
    ear_possible = []  # contiguous runs of head turn where a right-ear-only hit has > 0.01% chance
    for t in flat:
        on = t["codes"]["ear_only_right"] > 1e-4
        if on and (not ear_possible or ear_possible[-1][1] != prev):
            ear_possible.append([t["rel_deg"], t["rel_deg"]])
        elif on:
            ear_possible[-1][1] = t["rel_deg"]
        prev = t["rel_deg"]
    doc = dict(
        what="Chance of each outcome for ONE shot aimed at the centre of his head, by head pose. Integrated "
             "over the shot-spread model in dispersion.json.",
        source=source,
        rel_definition="0 = face pointing at the rifle; positive = face turned less far right than the rifle "
                       "line (90 = right ear toward the rifle, roughly facing the crowd); negative = turned past it.",
        ear_only_right_possible_rel_deg=ear_possible,
        rows=table)
    (out / "outcomes_by_turn.json").write_text(json.dumps(doc, indent=1))
    return source, doc["ear_only_right_possible_rel_deg"]


def export_dispersion(out):
    doc = dict(
        what="Shot-spread model. Each simulated engagement draws a shooter skill, a shared aim error and a "
             "range; then each shot lands at aim + bias + Gaussian scatter. Angles are minutes of angle "
             "(1 MOA = 4.04 cm at 139 m). The target plane is perpendicular to the line of fire: x = shooter's "
             "right, y = up.",
        priors=PRIORS, range_m=list(RANGE_M),
        sampling=["sigma = median * exp(N(0, log_sd)) from sigma_shot1_moa",
                  "ratio = U(vert_over_horiz); sx = sigma / sqrt(ratio); sy = sigma * sqrt(ratio)",
                  "bias_x ~ N(bias_x_moa), bias_y ~ N(bias_y_moa)", "range ~ U(range_m)",
                  "shot = aim + bias + N(0, sx|sy) [times followup_mult for quick follow-up shots]"],
        aim_point="Head aim = centre of the skull's bounding box.",
        sources={
            "Burcham 2018 (ARL-TR-8594)": "M4 + red-dot, 200 m pop-ups: 3.2 MOA per axis",
            "Tikuisis 2007 (DRDC TR 2006-258)": "125 m pop-ups: random 3.1 MOA plus a systematic offset about as large",
            "Norway SOF 2022 / Von Wahlde": "vertical scatter 1.0-1.25x horizontal",
            "notes": "/mnt/project-files/butler-shooting/benchmark-accuracy-notes.md",
        })
    (out / "dispersion.json").write_text(json.dumps(doc, indent=1))


def export_charts(out):
    d = out / "charts"
    d.mkdir(parents=True, exist_ok=True)
    from figures_views import by_rel_pitch_avg, shot_density, sweep_rows, video_pose
    rows, new = sweep_rows()
    rels, like = by_rel_pitch_avg(rows, lambda r: r["head"]["codes"]["ear_only_right"], lo=-60, hi=90)
    v = video_pose()
    prior = np.exp(-0.5 * ((rels - v["mean"]) / v["sd"]) ** 2) if v else np.ones_like(like)
    prior /= prior.sum()
    post = prior * like / (prior * like).sum()
    (d / "head_turn_inference.json").write_text(json.dumps(dict(
        what="Figure head_turn_inference.png: video prior x wound likelihood = combined estimate of head turn.",
        rel_deg=rels.tolist(), video_prior=prior.tolist(), video_pose=v,
        wound_likelihood_ear_only_right=like.tolist(), combined=post.tolist()), indent=1))
    flat = sorted([r for r in rows if r["pitch"] == 0 and r["roll"] == 0], key=lambda r: r["rel"])
    (d / "outcome_by_turn_curve.json").write_text(json.dumps(dict(
        what="Figures ear_exposure_by_head_turn.png / ear_only_vs_head_turn.png (pitch 0, roll 0).",
        from_current_sweep=new, rel_deg=[r["rel"] for r in flat],
        ear_only=[r["head"]["codes"]["ear_only_right"] + r["head"]["codes"]["ear_only_left"] for r in flat],
        buckets=[r["head"]["buckets"] for r in flat]), indent=1))
    g, dens = shot_density(np.zeros(2), half=420.0, step=6.0)
    (d / "shot_density.json").write_text(json.dumps(dict(
        what="Figure shot_heatmap_estimated_pose.png: probability per mm^2 that one head-aimed shot lands at "
             "(u, v) mm from the aim point. rows = v (ascending), cols = u (ascending).",
        axis_mm=g.tolist(), density_per_mm2=np.round(dens, 10).tolist()), indent=0))
    for f in ("summary.json", "sweep_v1.json"):
        if (RES / f).exists():
            shutil.copy(RES / f, d / f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    out = ap.parse_args().out
    out.mkdir(parents=True, exist_ok=True)
    glb = export_glb(out)
    n_maps = export_hitmaps(out)
    source, ear_range = export_outcomes(out)
    export_dispersion(out)
    export_charts(out)
    d = fire_direction(90.0, 0.8)
    print(json.dumps(dict(glb_faces=glb, hitmaps=n_maps, outcomes=source, ear_range=ear_range,
                          fire_direction_torso_frame=d.round(4).tolist(),
                          generated=dt.datetime.now(dt.timezone.utc).isoformat()), indent=1))


if __name__ == "__main__":
    main()
