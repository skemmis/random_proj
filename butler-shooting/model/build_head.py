"""Build the posed-ready 3D head: Trump likeness surface + fitted internal anatomy.

Inputs
  assets/bust/bust.glb        shortlan "Donald bust no shape keys" (Sketchfab, CC-BY), FBX converted with assimp
  assets/anatomy/*.ply        BodyParts3D 4.0 structures (CC-BY-SA 2.1 JP), mm, BP3D body frame

Output: assets/head_model/*.ply plus manifest.json, all in one "head frame":
  units mm, x = Trump's left, y = up, z = forward (out of the face),
  origin = midpoint of the two ear-canal openings (porion), so yaw/pitch are easy to read.

Steps
  1. Scale the bust uniformly so head length/breadth match ANSUR II men aged 50+ / 185 cm+
     (204 x 155 mm). The bust is a hand sculpt with no real-world units.
  2. (No subdivision: trimesh's loop subdivision distorts the sculpt's open patch borders.)
  3. Enlarge both auricles about their root so ear length is 73 mm (Heathcote 1995 age
     regression at 78; Trump's ears are visibly large). The bust's ears are ~60 mm after step 1.
  4. Map BodyParts3D into the bust frame, then fit it with an affine ICP of the BP3D head skin
     to the bust skin (cranium + face, ears and neck excluded). Apply the same transform to
     every internal structure, so skull, brain, vessels and spine sit inside the likeness.
  5. Add structures BodyParts3D lacks (external carotids, full-length internal jugulars).
"""

import json
import sys
from pathlib import Path

import numpy as np
import trimesh
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
ANAT = ROOT / "assets" / "anatomy"
BUST = ROOT / "assets" / "bust" / "bust.glb"
OUT = ROOT / "assets" / "head_model"

TARGET_HEAD_LENGTH = 204.0  # ANSUR II, men 50+ and >=185 cm, mean (data/ansur2_head_summary.md)
TARGET_HEAD_BREADTH = 155.0
TARGET_EAR_LENGTH = 73.0    # Heathcote 1995: 55.9 + 0.22 * 78 years
EAR_BREADTH_RATIO = 0.56    # ANSUR II men 50+/185 cm+: breadth 38.8 / length 68.4


def load_bust():
    s = trimesh.load(BUST)
    parts = {}
    for node in s.graph.nodes_geometry:
        T, g = s.graph[node]
        m = s.geometry[g].copy()
        m.apply_transform(T)
        parts[m.visual.material.name] = m
    return parts


def ear_mask(v, scale=1.0):
    """Auricle vertices on the raw bust (bust units, scaled by `scale`)."""
    v = v / scale
    return (np.abs(v[:, 0]) > 70) & (v[:, 2] > -100) & (v[:, 2] < 5) & (v[:, 1] > 395) & (v[:, 1] < 520)


def head_dims(v, scale=1.0):
    nv = v[~ear_mask(v, scale)]
    lo, hi = 470 * scale, 530 * scale
    band = nv[(nv[:, 1] > lo) & (nv[:, 1] < hi)]
    return band[:, 2].max() - band[:, 2].min(), band[:, 0].max() - band[:, 0].min()


def auricle_vertices(skin, side):
    """Vertices that belong to the auricle proper: lateral to the local scalp surface.

    We fit the scalp around the ear as a smooth function x(y, z) from non-ear vertices,
    then call ear anything sticking out more than 1.5 mm past it, plus a small dilation.
    """
    v = skin.vertices
    sgn = 1 if side == "left" else -1
    rough = ear_mask(v, SCALE) & (sgn * v[:, 0] > 0)
    lo, hi = v[rough].min(0) - 20, v[rough].max(0) + 20
    box = (sgn * v[:, 0] > 40) & np.all((v > lo) & (v < hi), axis=1)
    ring = box & ~rough
    # Quadratic surface fit of the scalp x(y, z) around the ear.
    P = v[ring]
    A = np.column_stack([np.ones(len(P)), P[:, 1], P[:, 2], P[:, 1] ** 2, P[:, 2] ** 2, P[:, 1] * P[:, 2]])
    coef, *_ = np.linalg.lstsq(A, sgn * P[:, 0], rcond=None)
    Q = v
    Aq = np.column_stack([np.ones(len(Q)), Q[:, 1], Q[:, 2], Q[:, 1] ** 2, Q[:, 2] ** 2, Q[:, 1] * Q[:, 2]])
    out = sgn * Q[:, 0] - Aq @ coef
    return rough & (out > 1.5), out, coef


SCALE = None


def build():
    global SCALE
    parts = load_bust()
    head = parts["HeadHires"]
    L, B = head_dims(head.vertices)
    SCALE = 0.5 * (TARGET_HEAD_LENGTH / L + TARGET_HEAD_BREADTH / B)
    print(f"bust head length {L:.1f}, breadth {B:.1f} (bust units) -> uniform scale {SCALE:.4f}")
    for m in parts.values():
        m.apply_scale(SCALE)

    skin = parts["HeadHires"]
    skin.merge_vertices()

    # --- anatomy in the bust frame -------------------------------------------------------
    manifest = json.loads((ANAT / "manifest.json").read_text())
    entries = manifest["files"]
    to_bust = np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1]], float)
    bp_skin = trimesh.load(ANAT / "skin_head_neck.ply")
    bp_skin.apply_transform(to_bust)

    # Region used for fitting: scalp/face above the ear-canal level, ears excluded on both
    # meshes. Fit = per-axis scale + translation + pitch (grid), by ICP. No shear, so the
    # anatomy keeps its shape and only stretches to the likeness's proportions.
    comps = skin.split(only_watertight=False)
    ear_comps = {("left" if c.centroid[0] > 0 else "right"): c for c in comps
                 if abs(c.centroid[0]) > 80 * SCALE and c.extents[1] < 90 * SCALE}
    assert set(ear_comps) == {"left", "right"}, "auricle patches not found"
    ear_y = np.mean([c.bounds[:, 1].mean() for c in ear_comps.values()])
    sv = skin.vertices
    on_ear = np.zeros(len(sv), bool)
    tree = cKDTree(np.vstack([c.vertices for c in ear_comps.values()]))
    on_ear[tree.query(sv)[0] < 1e-6] = True
    bust_fit = sv[(~on_ear) & (sv[:, 1] > ear_y)]

    bp_ears = trimesh.load(ANAT / "ear_external_left.ply"), trimesh.load(ANAT / "ear_external_right.ply")
    for e in bp_ears:
        e.apply_transform(to_bust)
    bp_ear_y = np.mean([e.bounds[:, 1].mean() for e in bp_ears])
    bpv = bp_skin.vertices
    near_ear = np.zeros(len(bpv), bool)
    for e in bp_ears:
        lo, hi = e.bounds
        near_ear |= np.all((bpv > lo - 4) & (bpv < hi + 4), axis=1)
    bp_fit = bpv[(~near_ear) & (bpv[:, 1] > bp_ear_y)]
    target = trimesh.Trimesh(sv, skin.faces, process=False)

    def icp(theta):
        R = trimesh.transformations.rotation_matrix(np.radians(theta), [1, 0, 0])[:3, :3]
        src0 = bp_fit @ R.T
        sc = np.ptp(bust_fit, axis=0) / np.ptp(src0, axis=0)
        tr = (bust_fit.max(0) + bust_fit.min(0)) / 2 - sc * (src0.max(0) + src0.min(0)) / 2
        for it in range(30):
            src = src0 * sc + tr
            closest, dist, _ = trimesh.proximity.closest_point(target, src)
            keep = dist < np.percentile(dist, 90)
            for a in range(3):
                A = np.column_stack([src0[keep, a], np.ones(keep.sum())])
                (sc[a], tr[a]), *_ = np.linalg.lstsq(A, closest[keep, a], rcond=None)
        M = np.eye(4)
        M[:3, :3] = np.diag(sc) @ R
        M[:3, 3] = tr
        return M, float(np.median(dist)), sc

    best = None
    for theta in range(-16, 17, 4):
        M_t, med, sc = icp(theta)
        print(f"  pitch {theta:+3d} deg: median fit error {med:.2f} mm, scales {sc.round(3)}")
        if best is None or med < best[1]:
            best = (M_t, med, theta)
    M = best[0]
    print(f"  chosen pitch {best[2]:+d} deg, median surface error {best[1]:.2f} mm")
    full = M @ to_bust
    place = fit_neck(full, skin, on_ear, bp_skin_raw=trimesh.load(ANAT / "skin_head_neck.ply"))

    # --- auricle enlargement ---------------------------------------------------------------
    ears_info = {}
    v = skin.vertices.copy()
    ear_flags = np.zeros(len(v), int)
    for side, code in (("left", 1), ("right", 2)):
        c = ear_comps[side]
        idx = tree_idx = cKDTree(c.vertices).query(v)[0] < 1e-6
        ev = v[idx]
        length = np.ptp(ev[:, 1])
        k = TARGET_EAR_LENGTH / length
        kz = TARGET_EAR_LENGTH * EAR_BREADTH_RATIO / np.ptp(ev[:, 2])
        sgn = 1 if side == "left" else -1
        medial = ev[np.argmin(sgn * ev[:, 0])]
        root = np.array([medial[0] - sgn * 2.0, ev[:, 1].min() + 0.55 * length, ev[:, 2].mean()])
        kx = 1 + 0.5 * (k - 1)  # protrusion grows less than length (keeps the ear attached)
        v[idx] = root + (ev - root) * np.array([kx, k, kz])
        ear_flags[idx] = code
        ears_info[side] = dict(length_before_mm=float(length), length_after_mm=float(np.ptp(v[idx][:, 1])),
                               scale_len=float(k), scale_protrusion=float(kx),
                               breadth_after_mm=float(np.ptp(v[idx][:, 2])))
        print(f"  {side} ear {length:.1f} mm -> {np.ptp(v[idx][:, 1]):.1f} mm long, "
              f"{np.ptp(v[idx][:, 2]):.1f} mm wide")
    skin.vertices = v

    # --- origin at mid-porion -----------------------------------------------------------
    porion = {}
    pts = {"left": (56.8, -83.6, 1505.6), "right": (-58.2, -83.7, 1505.7)}  # BP3D meatus (approx.)
    for side, p in pts.items():
        porion[side] = place(np.array([p]), cranial_only=True)[0]
    origin = (porion["left"] + porion["right"]) / 2
    shift = trimesh.transformations.translation_matrix(-origin)

    OUT.mkdir(parents=True, exist_ok=True)
    out_manifest = dict(neck_fit=FIT_INFO, fit_pitch_deg=best[2], fit_median_error_mm=best[1], frame="mm; x = Trump's left, y = up, z = forward (face); origin mid-porion",
                        bust_scale=SCALE, anatomy_affine=full.tolist(), ears=ears_info,
                        porion={k: (p - origin).tolist() for k, p in porion.items()}, files=[])

    def save(mesh, name, category, source):
        mesh = mesh.copy()
        mesh.apply_transform(shift)
        mesh.export(OUT / f"{name}.ply")
        out_manifest["files"].append(dict(name=name, file=f"{name}.ply", category=category, source=source,
                                          faces=int(len(mesh.faces)), bounds=mesh.bounds.round(1).tolist()))
        return mesh

    skin_out = save(skin, "skin_head", "skin", "bust")
    np.save(OUT / "skin_head_ear_flags.npy", ear_flags)
    save(parts["hair"], "hair", "hair", "bust")
    save(parts["Don_with_skeleton:Suit3:Suittexturematerial"], "suit", "clothing", "bust")
    save(parts["Teeth"], "bust_teeth", "other", "bust")

    for e in entries:
        f = e["file"]
        name = Path(f).stem
        if name in ("skin_head_neck", "ear_external_left", "ear_external_right"):
            continue
        m = trimesh.load(ANAT / f)
        rigid_with_skull = e.get("category") in ("skull", "brain", "brainstem", "other") and not name.startswith(
            ("hyoid", "esophagus", "cervical"))
        m.vertices = place(m.vertices, cranial_only=rigid_with_skull or name in ("mandible", "teeth"))
        save(m, name, e.get("category", "other"), "BodyParts3D 4.0 (CC-BY-SA 2.1 JP), affine-fitted")

    add_synthetic_vessels(place, save)
    (OUT / "manifest.json").write_text(json.dumps(out_manifest, indent=1))
    clearance_report(skin_out)
    return out_manifest


NECK_SCALE = 1.0


def fit_neck(full, skin, on_ear, bp_skin_raw):
    """Second fit for the neck, blended into the cranial fit.

    The cranial fit pitches BodyParts3D by about -12 deg, which swings its (neutral-posture)
    neck forward out of the bust's neck. Here we find a pitch about the C1/C2 joint plus
    left-right / front-back scaling that lays BP3D's neck skin onto the bust's neck skin, and
    blend from the cranial transform (above the dens) to the neck transform (below C3).
    Returns place(points_bp3d, cranial_only=False) -> points in bust frame.
    """
    global NECK_SCALE
    c2 = trimesh.load(ANAT / "vertebra_C2.ply")
    c2v = trimesh.transform_points(c2.vertices, full)
    pivot = np.array([0.0, c2v[:, 1].max(), np.median(c2v[:, 2])])
    y_hi = c2v[:, 1].max() - 10          # blend starts just below the dens
    y_lo = c2v[:, 1].min() - 15          # fully neck transform below C2/C3
    sv = skin.vertices
    neck_top = c2v[:, 1].min() - 5
    bust_neck = sv[(~on_ear) & (sv[:, 1] < neck_top) & (sv[:, 1] > sv[:, 1].min() + 8)]
    bpv = trimesh.transform_points(bp_skin_raw.vertices, full)
    target = trimesh.Trimesh(sv, skin.faces, process=False)

    def neck_T(phi, sx, sz, tx, tz):
        R = trimesh.transformations.rotation_matrix(np.radians(phi), [1, 0, 0], pivot)
        S = np.eye(4)
        S[0, 0], S[2, 2] = sx, sz
        S[:3, 3] = [tx + pivot[0] * (1 - sx), 0, tz + pivot[2] * (1 - sz)]
        return S @ R

    best = None
    for phi in range(-4, 33, 3):
        R = trimesh.transformations.rotation_matrix(np.radians(phi), [1, 0, 0], pivot)
        src_all = trimesh.transform_points(bpv, R)
        band = (src_all[:, 1] < neck_top) & (src_all[:, 1] > bust_neck[:, 1].min())
        src = src_all[band]
        if len(src) < 200:
            continue
        sx = sz = 1.0
        tx = tz = 0.0
        for it in range(20):
            cur = src.copy()
            cur[:, 0] = pivot[0] + sx * (src[:, 0] - pivot[0]) + tx
            cur[:, 2] = pivot[2] + sz * (src[:, 2] - pivot[2]) + tz
            closest, dist, _ = trimesh.proximity.closest_point(target, cur)
            keep = dist < np.percentile(dist, 85)
            for a in (0, 2):
                A = np.column_stack([src[keep, a] - pivot[a], np.ones(keep.sum())])
                (sc, tt), *_ = np.linalg.lstsq(A, closest[keep, a] - pivot[a], rcond=None)
                if a == 0:
                    sx, tx = sc, tt
                else:
                    sz, tz = sc, tt
        med = float(np.median(dist))
        print(f"  neck pitch {phi:+3d}: median error {med:.2f} mm (sx {sx:.3f}, sz {sz:.3f})")
        if best is None or med < best[0]:
            best = (med, phi, sx, sz, tx, tz)
    med, phi, sx, sz, tx, tz = best
    print(f"  neck: pitch {phi:+d} deg about C1/C2, scale x {sx:.3f} z {sz:.3f}, median error {med:.2f} mm")
    NECK_SCALE = float(np.sqrt(sx * sz))
    T_neck = neck_T(phi, sx, sz, tx, tz) @ full
    FIT_INFO.update(neck_pitch_deg=phi, neck_scale_x=sx, neck_scale_z=sz, neck_median_error_mm=med)

    def place(points, cranial_only=False):
        a = trimesh.transform_points(np.asarray(points, float), full)
        if cranial_only:
            return a
        b = trimesh.transform_points(np.asarray(points, float), T_neck)
        w = np.clip((y_hi - a[:, 1]) / (y_hi - y_lo), 0, 1)[:, None]
        return a * (1 - w) + b * w

    return place


FIT_INFO = {}


def tube(points, radius, sections=14):
    """Swept circular tube along a polyline (closed caps via convex hulls per segment)."""
    pieces = []
    for a, b in zip(points[:-1], points[1:]):
        seg = trimesh.creation.cylinder(radius=radius, segment=[a, b], sections=sections)
        pieces.append(seg)
        pieces.append(trimesh.creation.icosphere(subdivisions=1, radius=radius).apply_translation(b))
    return trimesh.util.concatenate(pieces)


def add_synthetic_vessels(place, save):
    """External carotids and full internal jugulars, routed between BP3D landmarks.

    BodyParts3D 4.0 has no external carotid, and its internal jugular is a 44 mm segment.
    Routes are drawn in BP3D coordinates from standard anatomy (bifurcation at C3/C4 level,
    external carotid running up behind the mandibular ramus to the parotid region; internal
    jugular from the jugular foramen down lateral to the carotid sheath).
    """
    for side, sgn in (("left", 1), ("right", -1)):
        cc = trimesh.load(ANAT / f"artery_common_carotid_{side}.ply")
        ic = trimesh.load(ANAT / f"artery_internal_carotid_{side}.ply")
        top_cc = cc.vertices[cc.vertices[:, 2].argmax()]
        bif = top_cc
        # Cervical internal carotid: bifurcation up to where BP3D's vessel enters the skull base.
        ic_entry = ic.vertices[ic.vertices[:, 2].argmin()]
        path = np.array([bif + t * (ic_entry - bif) + [0, 6 * np.sin(np.pi * t), 0] for t in np.linspace(0, 1, 7)])
        m = tube(place(path), 2.8 * NECK_SCALE)
        save(m, f"artery_internal_carotid_cervical_{side}", "artery", "synthetic route (BP3D starts at skull base)")
        ext = np.array([bif,
                        bif + [sgn * 4, -8, 18],
                        bif + [sgn * 10, -14, 40],
                        bif + [sgn * 16, -12, 62]])  # ends near the neck of the mandible
        m = tube(place(ext), 2.6 * NECK_SCALE)
        save(m, f"artery_external_carotid_{side}", "artery", "synthetic route (BP3D lacks it)")
        # Internal jugular: from jugular foramen (just lateral/posterior to the internal carotid's
        # skull entry) down beside the common carotid to the BP3D segment / subclavian junction.
        ic_low = ic.vertices[ic.vertices[:, 2].argmin()]
        cc_low = cc.vertices[cc.vertices[:, 2].argmin()]
        top = ic_low + [sgn * 8, 10, 4]
        path = [top]
        for t in np.linspace(0.15, 1.0, 6):
            p = top + t * (cc_low + [sgn * 14, -2, 0] - top)
            path.append(p)
        m = tube(place(np.array(path)), 6.0 * NECK_SCALE)
        save(m, f"vein_internal_jugular_full_{side}", "vein", "synthetic route (BP3D segment is partial)")


def clearance_report(skin):
    """How far inside the skin the skull sits (positive = inside)."""
    sk = trimesh.load(OUT / "skull_cranium.ply")
    pts = sk.vertices[:: max(1, len(sk.vertices) // 20000)]
    closest, dist, tri = trimesh.proximity.closest_point(skin, pts)
    n = skin.face_normals[tri]
    signed = np.einsum("ij,ij->i", closest - pts, n)  # > 0 when the point is inside (behind the surface)
    upper = pts[:, 1] > 0
    print(f"skull-to-skin clearance (cranial vault, y>0): min {signed[upper].min():.1f} mm, "
          f"5th pct {np.percentile(signed[upper], 5):.1f}, median {np.median(signed[upper]):.1f}")


if __name__ == "__main__":
    build()
