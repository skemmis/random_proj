"""3D hit simulation: benchmark shot dispersion ray-cast through a posed Trump likeness.

World frame = Trump's torso frame, in mm: x = his left, y = up, z = the way his torso faces.
Origin = midpoint of his ear canals with the head in neutral pose.

Geometry knobs (all angles in degrees)
  shooter_az   where the shooter is, measured from Trump's torso-forward direction toward his
               right (90 = 3 o'clock). Research notes put the AGR roof at about 3 o'clock.
  head_yaw     head turn to his right relative to the torso (he had turned toward the chart).
  head_pitch   chin up (+) / down (-).
  elev         how far the bullet is descending as it arrives (shooter higher), ~0.6-1.0.

The quantity that really matters is rel = shooter_az - head_yaw: the angle between where his
face points and where the shooter is. rel = 0: face to the shooter. rel = 90: right ear to the
shooter (Sam's point: an "ear" hit then goes straight into the skull).

Each bullet is a 5.7 mm cylinder, approximated by its centreline plus six rays on its rim. A
structure counts as hit if any of the seven rays crosses it.

Outcome buckets (most severe structure along the path wins):
  killed_or_wounded: brain/brainstem/spinal cord, major vessel, skull/jaw/spine bone, airway,
                     eye, torso, or any path deeper than GRAZE_DEPTH_MM into the soft tissue of
                     the scalp, face or neck
  grazed:            the headline (Sam, 2026-10-13: "grazed but not lethal"): the ear, and/or no
                     more than the outer GRAZE_DEPTH_MM of skin anywhere on the head or neck.
                     Ear-only paths (the actual wound) are reported as a subset.
  arm:               a hit on the arm only
  miss:              no tissue (hair-only passes are counted as misses and tallied separately)
"""

import json
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import trimesh

sys.path.insert(0, str(Path(__file__).parent))
from dispersion import PRIORS, moa_to_cm, sample_engagements  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
HM = ROOT / "assets" / "head_model"
BULLET_RADIUS_MM = 2.85
HEAD_PIVOT = np.array([0.0, -30.0, -15.0])  # top of C2 (dens), about which the head turns

GROUPS = {
    "brain": ["cerebrum_left", "cerebrum_right", "cerebellum", "brainstem_midbrain", "brainstem_pons",
              "brainstem_medulla", "spinal_cord_cervical", "pituitary", "ventricular_system"],
    "vessel": ["artery_common_carotid_left", "artery_common_carotid_right", "artery_internal_carotid_left",
               "artery_internal_carotid_right", "artery_internal_carotid_cervical_left",
               "artery_internal_carotid_cervical_right", "artery_external_carotid_left",
               "artery_external_carotid_right", "artery_vertebral_left", "artery_vertebral_right",
               "artery_basilar", "artery_subclavian_left", "artery_subclavian_right",
               "artery_brachiocephalic_trunk", "vein_internal_jugular_left", "vein_internal_jugular_right",
               "vein_internal_jugular_full_left", "vein_internal_jugular_full_right",
               "vein_subclavian_left", "vein_subclavian_right"],
    "bone": ["skull_cranium", "mandible", "teeth", "hyoid", "cervical_discs"] + [f"vertebra_C{i}" for i in range(1, 8)],
    "airway": ["trachea", "larynx", "esophagus"],
    "eye": ["eyeball_left", "eyeball_right"],
}
VITAL_ORDER = ["brain", "vessel", "bone", "airway", "eye", "torso", "deep_soft"]
GRAZE_DEPTH_MM = 4.0  # Sam, 2026-10-13: deeper than skin (2-3 mm), short of the skull (~6 mm)


def inner_skin(skin, not_ear_faces, depth=GRAZE_DEPTH_MM):
    """The scalp, face and neck skin moved `depth` mm inward along its normals. A bullet path
    that crosses this shell has gone deeper than a graze."""
    sub = skin.submesh([np.where(not_ear_faces)[0]], append=True)
    n = sub.vertex_normals.copy()
    # A few bust patches are wound inside-out; flip their normals so every offset goes inward.
    for comp in trimesh.graph.connected_components(sub.face_adjacency, nodes=np.arange(len(sub.faces))):
        verts = np.unique(sub.faces[comp])
        if np.mean(np.einsum("ij,ij->i", sub.face_normals[comp], sub.triangles_center[comp])) < 0:
            n[verts] *= -1
    shell = sub.copy()
    shell.vertices = sub.vertices - depth * n
    return shell


def _load(name):
    return trimesh.load(HM / f"{name}.ply", process=False)


@lru_cache(maxsize=1)
def base_meshes():
    """Head-attached meshes grouped by role, in the neutral head pose."""
    skin = _load("skin_head")
    flags = np.load(HM / "skin_head_ear_flags.npy")
    fflag = flags[skin.faces].max(axis=1)  # face is ear if any vertex is
    c = skin.triangles_center
    ear_r = fflag == 2
    ear_l = fflag == 1
    not_ear = ~(ear_r | ear_l)
    # Face soft tissue: in front of the ears, below the brow line, above the chin.
    face = not_ear & (c[:, 2] > 25) & (c[:, 1] < 45) & (c[:, 1] > -75)
    neck = not_ear & ~face & (c[:, 1] < -45)
    scalp = not_ear & ~face & ~neck
    head = {
        "ear_right": skin.submesh([np.where(ear_r)[0]], append=True),
        "ear_left": skin.submesh([np.where(ear_l)[0]], append=True),
        "face": skin.submesh([np.where(face)[0]], append=True),
        "neck": skin.submesh([np.where(neck)[0]], append=True),
        "scalp": skin.submesh([np.where(scalp)[0]], append=True),
        "hair": _load("hair"),
        "deep_soft": inner_skin(skin, not_ear),
    }
    for g, names in GROUPS.items():
        head[g] = trimesh.util.concatenate([_load(n) for n in names])
    return head


@lru_cache(maxsize=1)
def body_meshes():
    """Torso and arms, fixed to the torso frame (they don't turn with the head)."""
    suit = _load("suit")
    v = suit.vertices
    low = v[v[:, 1] < v[:, 1].min() + 30]
    cx, cz = (low[:, 0].max() + low[:, 0].min()) / 2, (low[:, 2].max() + low[:, 2].min()) / 2
    ax, az = np.ptp(low[:, 0]) / 2 * 0.92, np.ptp(low[:, 2]) / 2 * 0.92
    y0, y1 = -820.0, v[:, 1].min() + 10  # down to the belt line, ~0.82 m below the ear canals
    cyl = trimesh.creation.cylinder(radius=1.0, height=y1 - y0, sections=48)
    cyl.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    cyl.apply_scale([ax, 1, az])
    cyl.apply_translation([cx, (y0 + y1) / 2, cz])
    # The bust's suit is an open shell (armholes, open shirt front), so the solid torso is the
    # convex hull of the suit below the base of the neck, plus the cylinder down to the belt.
    # The collar above y = -140 stays as a thin shell so the neck itself is still modelled by
    # its skin and anatomy, not swallowed by the hull.
    below = v[v[:, 1] < -140.0]
    hull = trimesh.convex.convex_hull(below)
    collar = suit.submesh([np.where(suit.triangles_center[:, 1] >= -140.0)[0]], append=True)
    torso = trimesh.util.concatenate([hull, cyl, collar])
    arms = []
    for sgn in (1, -1):
        sh = np.array([sgn * (ax + 35), -150.0, cz])
        el = np.array([sgn * (ax + 45), -470.0, cz + 30])
        wr = np.array([sgn * (ax + 10), -560.0, cz + 280])  # forearms forward, hands on the lectern
        arms += [trimesh.creation.capsule(height=np.linalg.norm(el - sh), radius=50).apply_transform(
                     trimesh.geometry.align_vectors([0, 0, 1], el - sh)).apply_translation((sh + el) / 2),
                 trimesh.creation.capsule(height=np.linalg.norm(wr - el), radius=40).apply_transform(
                     trimesh.geometry.align_vectors([0, 0, 1], wr - el)).apply_translation((el + wr) / 2)]
    return {"torso": torso, "arm": trimesh.util.concatenate(arms)}


def head_rotation(yaw, pitch=0.0, roll=0.0):
    """4x4 transform turning the head about the dens. yaw > 0 = turned to his right."""
    R = (trimesh.transformations.rotation_matrix(np.radians(-yaw), [0, 1, 0], HEAD_PIVOT)
         @ trimesh.transformations.rotation_matrix(np.radians(-pitch), [1, 0, 0], HEAD_PIVOT)
         @ trimesh.transformations.rotation_matrix(np.radians(roll), [0, 0, 1], HEAD_PIVOT))
    return R


class Scene:
    def __init__(self, head_yaw, head_pitch=0.0, head_roll=0.0):
        T = head_rotation(head_yaw, head_pitch, head_roll)
        self.T = T
        self.meshes = {}
        for k, m in base_meshes().items():
            mm = m.copy()
            mm.apply_transform(T)
            self.meshes[k] = mm
        self.meshes.update(body_meshes())

    def hits(self, origins, dirs):
        return {k: m.ray.intersects_any(origins, dirs) for k, m in self.meshes.items()}


def fire_direction(shooter_az, elev):
    """Unit vector of bullet travel (from shooter toward Trump), torso frame."""
    a, e = np.radians(shooter_az), np.radians(elev)
    to_shooter = np.array([-np.sin(a) * np.cos(e), np.sin(e), np.cos(a) * np.cos(e)])
    return -to_shooter


def plane_basis(d):
    up = np.array([0.0, 1.0, 0.0])
    right = np.cross(d, up)
    right /= np.linalg.norm(right)
    true_up = np.cross(right, d)
    return right, true_up


def aim_points(scene, d):
    """Head aim = centre of the cranium (what you'd put a dot on); chest aim = mid-sternum height."""
    sk = scene.meshes["bone"]
    skull_c = trimesh.load(HM / "skull_cranium.ply", process=False).bounds.mean(0)
    head_c = trimesh.transform_points(skull_c[None], scene.T)[0]
    torso = body_meshes()["torso"]
    chest = np.array([0.0, -330.0, torso.bounds[:, 2].mean()])
    return {"head": head_c, "chest": chest}


def classify(h):
    """h: dict group -> bool array (per bullet, OR over the 7 rays). Returns label array."""
    n = len(next(iter(h.values())))
    out = np.full(n, "miss", dtype=object)
    hair_only = h["hair"].copy()
    ear = h["ear_right"] | h["ear_left"]
    skin = h["scalp"] | h["face"] | h["neck"]
    vital = np.zeros(n, bool)
    vital_kind = np.full(n, "", dtype=object)
    for g in VITAL_ORDER:
        sel = h[g] & ~vital
        vital_kind[sel] = g
        vital |= h[g]
    out[(ear | skin) & ~vital] = "grazed"
    out[h["arm"] & ~(ear | skin) & ~vital] = "arm"
    out[vital] = "killed_or_wounded"
    hair_only &= out == "miss"
    return out, vital_kind, hair_only


def simulate(n, rng, aim="head", shooter_az=90.0, head_yaw=0.0, head_pitch=0.0, elev=0.8,
             followup=False, scene=None, return_points=False, priors=PRIORS):
    if scene is None:
        scene = Scene(head_yaw, head_pitch)
    d = fire_direction(shooter_az, elev)
    right, up = plane_basis(d)
    e = sample_engagements(n, rng, priors)
    mult = 1.0
    if followup:
        f = priors["followup_mult"]
        mult = f["median"] * np.exp(rng.normal(0, f["log_sd"], n))
    x_moa = e["bx"] + rng.normal(0, 1, n) * e["sx"] * mult
    y_moa = e["by"] + rng.normal(0, 1, n) * e["sy"] * mult
    dx = moa_to_cm(x_moa, e["range_m"]) * 10.0  # mm
    dy = moa_to_cm(y_moa, e["range_m"]) * 10.0
    centre = aim_points(scene, d)[aim]
    pts = centre + dx[:, None] * right + dy[:, None] * up
    origins0 = pts - d * 3000.0
    k = 7
    ang = np.linspace(0, 2 * np.pi, 7)[:-1]
    offs = [np.zeros(3)] + [BULLET_RADIUS_MM * (np.cos(a) * right + np.sin(a) * up) for a in ang]
    origins = np.concatenate([origins0 + o for o in offs])
    dirs = np.tile(d, (len(origins), 1))
    raw = scene.hits(origins, dirs)
    h = {g: v.reshape(k, n).any(axis=0) for g, v in raw.items()}
    labels, vital_kind, hair_only = classify(h)
    res = dict(labels=labels, vital_kind=vital_kind, hair_only=hair_only, hits=h)
    if return_points:
        res.update(dx=dx, dy=dy, right=right, up=up, d=d, centre=centre)
    return res


def summarize(res):
    lab = res["labels"]
    out = {k: float(np.mean(lab == k)) for k in ("grazed", "killed_or_wounded", "arm", "miss")}
    out["miss_hair_only"] = float(np.mean(res["hair_only"]))
    vk = res["vital_kind"]
    out["vital_breakdown"] = {g: float(np.mean(vk == g)) for g in VITAL_ORDER}
    return out


if __name__ == "__main__":
    rng = np.random.default_rng(13072024)
    for rel in (0, 30, 60, 90):
        r = simulate(50_000, rng, aim="head", shooter_az=90.0, head_yaw=90.0 - rel)
        print(rel, json.dumps({k: (round(v, 5) if isinstance(v, float) else v) for k, v in summarize(r).items()
                               if k != "vital_breakdown"}))
