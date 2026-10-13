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
    full = refine_by_tissue_depth(full, skin, on_ear) @ full
    face_warp = make_face_warp(full, skin)
    side_warp = make_lateral_warp(full, face_warp, skin, on_ear)
    warp = lambda p: side_warp(face_warp(p))
    place = fit_neck(full, skin, on_ear, bp_skin_raw=trimesh.load(ANAT / "skin_head_neck.ply"), warp=warp)

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
    export_textures(parts)
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


def fit_neck(full, skin, on_ear, bp_skin_raw, warp=None):
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
        if warp is not None:
            a = warp(a)
        if cranial_only:
            return a
        b = trimesh.transform_points(np.asarray(points, float), T_neck)
        w = np.clip((y_hi - a[:, 1]) / (y_hi - y_lo), 0, 1)[:, None]
        return a * (1 - w) + b * w

    return place


FIT_INFO = {}

# Soft-tissue depth over the cranial vault, adult men (forensic facial-reconstruction tables,
# e.g. De Greef et al. 2006; Stephan & Simpson 2008): about 5-6 mm at the vertex, forehead and
# occiput, and about 10-12 mm over the temporal fossa where the temporalis muscle sits.
TISSUE_VAULT_MM = 5.8
TISSUE_TEMPORAL_MM = 6.0  # set to the vault value: Sam judged the skull too narrow at 11 mm


def refine_by_tissue_depth(full, skin, on_ear):
    """Re-fit the cranium so the skin sits a realistic tissue depth outside the skull.

    The first fit matched BodyParts3D's skin to the bust's skin, which leaves the skull
    wherever BP3D's own scalp put it (gaps of 8-9 mm on top, under 1 mm at the forehead).
    Sam flagged the skull as looking too small. Here we adjust per-axis scale, translation and
    pitch of the cranial transform so the skull-to-skin gap along each outer-skull normal
    matches the tissue-depth targets above. Returns a 4x4 correction applied after `full`.
    """
    from scipy.optimize import least_squares
    sk = trimesh.load(ANAT / "skull_cranium.ply")
    sk.apply_transform(full)
    # Outer-surface vault points: vertices whose normal points away from the skull centre and
    # whose outward ray does not hit the skull again.
    c = sk.bounds.mean(0)
    v, n = sk.vertices, sk.vertex_normals
    outward = np.einsum("ij,ij->i", v - c, n) > 0
    vault = outward & (v[:, 1] > c[1] - 15)
    idx = np.where(vault)[0][:: max(1, vault.sum() // 6000)]
    again = sk.ray.intersects_any(v[idx] + n[idx] * 0.5, n[idx])
    idx = idx[~again]
    # Temporal fossa: lateral points below the temporal lines (approx. |x| > 50, low on vault,
    # in front of the ear canal-ish region).
    p0 = v[idx]
    temporal = (np.abs(p0[:, 0] - c[0]) > 52) & (p0[:, 1] < c[1] + 25) & (p0[:, 2] > c[2] - 40)
    target = np.where(temporal, TISSUE_TEMPORAL_MM, TISSUE_VAULT_MM)
    skin_no_ear = skin.submesh([np.where(~on_ear[skin.faces].any(axis=1))[0]], append=True)
    pairs = landmark_pairs(full, skin)
    lm_p = np.array([p[1] for p in pairs])
    lm_goal = np.array([p[2] for p in pairs])
    lm_mask = np.array([p[3] for p in pairs], float)
    w_lm = np.sqrt(len(p0) / len(pairs))

    def correction(x):
        sx, sy, sz, tx, ty, tz, pitch = x
        R = trimesh.transformations.rotation_matrix(np.radians(pitch), [1, 0, 0], c)
        S = np.diag([sx, sy, sz, 1.0])
        S[:3, 3] = c - np.array([sx, sy, sz]) * c + [tx, ty, tz]
        return S @ R

    def resid(x):
        T = correction(x)
        p = trimesh.transform_points(p0, T)
        nn = trimesh.transform_points(p0 + n[idx], T) - p
        nn /= np.linalg.norm(nn, axis=1, keepdims=True)
        locs, ray, _ = skin_no_ear.ray.intersects_location(p, nn, multiple_hits=False)
        gap = np.full(len(p), 30.0)
        gap[ray] = np.einsum("ij,ij->i", locs - p[ray], nn[ray])
        # Skull poking through the skin: the outward ray misses or the gap is huge; also
        # check inward so negative gaps are seen.
        locs2, ray2, _ = skin_no_ear.ray.intersects_location(p, -nn, multiple_hits=False)
        inside_miss = np.setdiff1d(ray2, ray)
        gap[inside_miss] = -np.einsum("ij,ij->i", locs2[np.isin(ray2, inside_miss)] - p[inside_miss],
                                      -nn[inside_miss])
        err = np.clip(gap - target, -20, 20)
        # Bone may never come closer than 3 mm to the surface: penalise that 5x.
        err = np.where(gap < 3.0, 5.0 * err, err)
        return np.concatenate([err, w_lm * landmark_errors(T)])

    def landmark_errors(T):
        p = trimesh.transform_points(lm_p, T)
        return np.clip(((p - lm_goal) * lm_mask).sum(axis=1), -25, 25)

    x0 = np.array([1, 1, 1, 0, 0, 0, 0], float)
    r0 = resid(x0)
    sol = least_squares(resid, x0, diff_step=1e-3, loss="soft_l1", f_scale=2.0,
                        bounds=([0.85, 0.85, 0.85, -15, -15, -15, -10], [1.25, 1.25, 1.25, 15, 15, 15, 10]))
    r1 = resid(sol.x)
    e0, e1 = landmark_errors(correction(x0)), landmark_errors(correction(sol.x))
    for (name, *_), a, b in zip(pairs, e0, e1):
        print(f"    {name:18s} bone-vs-target error {a:+6.1f} -> {b:+6.1f} mm")
    print(f"  tissue-depth refit: scale {sol.x[:3].round(3)}, shift {sol.x[3:6].round(1)} mm, "
          f"pitch {sol.x[6]:+.1f} deg; gap error median {np.median(np.abs(r0)):.1f} -> "
          f"{np.median(np.abs(r1)):.1f} mm")
    FIT_INFO.update(tissue_refit=dict(scale=sol.x[:3].tolist(), shift_mm=sol.x[3:6].tolist(),
                                      pitch_deg=float(sol.x[6]), median_abs_gap_error_mm=float(np.median(np.abs(r1)))))
    return correction(sol.x)


# Midline/facial soft-tissue depths for adult men, mm (De Greef et al. 2006, Forensic Sci Int
# 159S: S126-S146, BMI-normal males; rounded). Direction is the skin-normal direction we probe.
FACE_TISSUE = {"glabella": 5.6, "nasion": 6.5, "rhinion": 2.9, "upper_lip": 12.9, "lower_lip": 14.0,
               "chin_lip_fold": 11.0, "pogonion": 11.5, "menton": 7.6, "zygion": 7.0, "gonion": 13.0}


def skin_profile_landmarks(skin):
    """Soft-tissue landmarks on the bust's midline profile (bust frame, mm)."""
    # Ray-cast the profile from in front (robust to the sculpt's patch seams on the midline):
    # median over three parallel rays 2.5 mm either side of the midline.
    c = skin.bounds.mean(0)
    ys = np.arange(skin.bounds[0, 1], skin.bounds[1, 1], 1.0)
    zs = []
    for x in (-2.5, 0.0, 2.5):
        o = np.column_stack([np.full(len(ys), x), ys, np.full(len(ys), skin.bounds[1, 2] + 50)])
        d = np.tile([0, 0, -1.0], (len(ys), 1))
        locs, ray, _ = skin.ray.intersects_location(o, d, multiple_hits=False)
        zz = np.full(len(ys), np.nan)
        zz[ray] = locs[:, 2]
        zs.append(zz)
    z = np.nanmedian(np.array(zs), axis=0)
    z[z < c[2]] = np.nan  # only the face side
    front = np.column_stack([np.zeros(np.isfinite(z).sum()), ys[np.isfinite(z)], z[np.isfinite(z)]])

    def arg(fn, lo, hi):
        m = (ys >= lo) & (ys <= hi) & np.isfinite(z)
        i = np.where(m)[0][fn(z[m])]
        return np.array([0.0, ys[i], z[i]])

    prn = arg(np.argmax, ys.min(), ys.max())
    sn = arg(np.argmin, prn[1] - 32, prn[1] - 10)
    ls = arg(np.argmax, sn[1] - 18, sn[1] - 4)
    sto = arg(np.argmin, ls[1] - 14, ls[1] - 3)
    li = arg(np.argmax, sto[1] - 12, sto[1] - 2)
    fold = arg(np.argmin, li[1] - 25, li[1] - 6)
    pog = arg(np.argmax, fold[1] - 30, fold[1] - 6)
    # Menton: bottom of the chin, found by casting rays upward under the chin.
    zz = np.arange(pog[2] - 30, pog[2] - 2, 1.0)
    o = np.column_stack([np.zeros(len(zz)), np.full(len(zz), pog[1] - 80), zz])
    locs, ray, _ = skin.ray.intersects_location(o, np.tile([0, 1.0, 0], (len(zz), 1)), multiple_hits=False)
    under = locs[locs[:, 1] < pog[1]]
    me = under[under[:, 1].argmin()] if len(under) else np.array([0, pog[1] - 15, pog[2] - 12])
    me = np.array([0.0, me[1], me[2]])
    n = arg(np.argmin, prn[1] + 25, prn[1] + 60)
    g = arg(np.argmax, n[1] + 5, n[1] + 30)
    return dict(pronasale=prn, subnasale=sn, labrale_sup=ls, stomion=sto, labrale_inf=li,
                labiomental_fold=fold, pogonion=pog, menton=me, nasion=n, glabella=g)


LATERAL_TISSUE_MM = 6.0
MIN_SIDE_TISSUE_MM = 4.0
EAR_ROOT_TISSUE_MM = 6.0  # skin + cartilage between the ear's root and the temporal bone


def make_lateral_warp(full, face_warp, skin, on_ear):
    """Widen (or narrow) the cranium side to side so its sides sit LATERAL_TISSUE_MM under the
    bust's skin at every height and depth (Sam: "the skull is too narrow for the Trump model"),
    and EAR_ROOT_TISSUE_MM under the root of each ear (Sam: "the sides of the skull don't
    connect to the ears").

    We measure the gap on a (y, z) grid by casting rays sideways from the midline, counting the
    ears as skin (the ear patch is a hole in the rest of the skin, so without them the ear zone
    had no measurement and was left unwidened), smooth it, and move each point outward by
    x * (s(y, z) - 1) * h(|x|). h ramps from 0 near the midline to 1 at the skull wall, so the
    skull sides move while midline structures (brainstem, carotids, spine) stay put. In front
    of the ears and below the cheekbones, where real soft tissue is thick (cheeks, jowls), the
    warp fades out; behind the cheek it continues down to the bottom of the ear lobes.
    """
    from scipy.ndimage import gaussian_filter
    from scipy.interpolate import RegularGridInterpolator
    sk = trimesh.load(ANAT / "skull_cranium.ply")
    sk.apply_transform(full)
    sk.vertices = face_warp(sk.vertices)
    ear_face = on_ear[skin.faces].any(axis=1)
    ev = skin.vertices[on_ear]
    ear_ymin, ear_zmax = float(ev[:, 1].min()), float(ev[:, 2].max())
    gy = np.arange(sk.bounds[0, 1] - 10, sk.bounds[1, 1] + 10, 4.0)
    gz = np.arange(sk.bounds[0, 2] - 10, sk.bounds[1, 2] + 10, 4.0)
    Y, Zg = np.meshgrid(gy, gz, indexing="ij")
    ratio = np.full(Y.shape + (2,), np.nan)
    cap = np.full(Y.shape + (2,), np.nan)
    for k, sgn in enumerate((1, -1)):
        o = np.column_stack([np.zeros(Y.size), Y.ravel(), Zg.ravel()])
        d = np.tile([sgn, 0, 0.0], (Y.size, 1))
        ls, rs, _ = sk.ray.intersects_location(o, d)
        lk, rk, tk = skin.ray.intersects_location(o, d)
        sk_x = np.full(Y.size, np.nan)
        np.fmax.at(sk_x, rs, np.abs(ls[:, 0]))
        # Innermost skin or ear surface along the ray (the ear's medial face is its root).
        keep = np.abs(lk[:, 0]) > 20
        sn_x = np.full(Y.size, np.inf)
        np.minimum.at(sn_x, rk[keep], np.abs(lk[keep, 0]))
        hit_ear = np.zeros(Y.size, bool)
        first = np.full(Y.size, np.inf)
        np.minimum.at(first, rk[keep], np.abs(lk[keep, 0]))
        is_first = keep & (np.abs(lk[:, 0]) == first[rk])
        hit_ear[rk[is_first & ear_face[tk]]] = True
        sn_x[~np.isfinite(sn_x)] = np.nan
        ok = np.isfinite(sk_x) & np.isfinite(sn_x) & (sk_x > 20)
        r = np.full(Y.size, np.nan)
        # 6 mm over the upper vault; 9 mm low on the side, where the temporalis muscle lies;
        # EAR_ROOT_TISSUE_MM where the ray meets the ear.
        tgt = LATERAL_TISSUE_MM + 3.0 * np.clip((40.0 - Y.ravel()) / 25.0, 0, 1)
        tgt = np.where(hit_ear, EAR_ROOT_TISSUE_MM, tgt)
        r[ok] = (sn_x[ok] - tgt[ok]) / sk_x[ok]
        ratio[..., k] = r.reshape(Y.shape)
        c = np.full(Y.size, np.nan)
        c[ok] = (sn_x[ok] - MIN_SIDE_TISSUE_MM) / sk_x[ok]
        cap[..., k] = c.reshape(Y.shape)
    sc = np.nanmean(ratio, axis=2)
    cap = np.nanmin(cap, axis=2)
    have = np.isfinite(sc)
    sc = np.clip(np.where(have, sc, 1.0), 0.94, 1.35)
    w = gaussian_filter(have.astype(float), 1.5)
    sc = 1.0 + gaussian_filter(np.where(have, sc - 1.0, 0.0), 1.5) / np.maximum(w, 1e-3) * (w > 0.05)
    # Fade out below the zygomatic arches in front of the ear (cheeks and jowls have thick
    # soft tissue); behind that, carry the widening down to just below the ear lobes.
    zyg = trimesh.util.concatenate([trimesh.load(ANAT / f"bone_{s}_zygomatic_bone.ply") for s in ("left", "right")])
    zyg.apply_transform(full)
    zyg_y = float(np.median(face_warp(zyg.vertices)[:, 1]))
    fade_face = np.clip((Y - (zyg_y - 20)) / 15.0, 0, 1)
    fade_ear = np.clip((Y - (ear_ymin - 12)) / 12.0, 0, 1)
    behind_cheek = np.clip((ear_zmax + 15 - Zg) / 15.0, 0, 1)
    fade = np.maximum(fade_face, behind_cheek * fade_ear)
    sc = 1.0 + (sc - 1.0) * fade
    # Smoothing spreads the ear-root widening onto its neighbours; never push the skull wall
    # closer than MIN_SIDE_TISSUE_MM to the skin where we measured it.
    sc = np.where(np.isfinite(cap) & (sc > 1.0), np.minimum(sc, np.maximum(cap, 1.0)), sc)
    interp = RegularGridInterpolator((gy, gz), sc, bounds_error=False, fill_value=1.0)
    print(f"  lateral warp: side-to-side scale {sc[have].min():.3f}-{sc[have].max():.3f} "
          f"(median {np.median(sc[have]):.3f})")
    FIT_INFO["lateral_warp"] = dict(target_mm=LATERAL_TISSUE_MM, ear_root_target_mm=EAR_ROOT_TISSUE_MM,
                                    scale_min=float(sc[have].min()), scale_max=float(sc[have].max()),
                                    scale_median=float(np.median(sc[have])))

    def warp(points):
        p = np.asarray(points, float).copy()
        t = np.clip((np.abs(p[:, 0]) - 15.0) / 25.0, 0, 1)
        h = t * t * (3 - 2 * t)
        p[:, 0] *= 1.0 + (interp(p[:, 1:3]) - 1.0) * h
        return p

    return warp


def make_face_warp(full, skin):
    """Smooth deformation of the facial skeleton so the jaw, teeth and nose sit behind the
    bust's chin, lips and nose at realistic tissue depths, while the vault stays put.

    The bust's face is longer and less protruding relative to its cranium than BodyParts3D's,
    so one affine transform cannot fit both (Sam spotted the jaw sitting too high). We use a
    Gaussian radial-basis warp: the landmark displacements are the (masked) bone-to-target
    offsets from landmark_pairs(); a ring of vault and skull-base anchor points has zero
    displacement, and the warp fades to zero far from the face.
    """
    from scipy.interpolate import RBFInterpolator
    pairs = landmark_pairs(full, skin)
    P = np.array([p[1] for p in pairs])
    D = np.array([(p[2] - p[1]) * p[3] for p in pairs])
    sk = trimesh.load(ANAT / "skull_cranium.ply")
    sk.apply_transform(full)
    v = sk.vertices
    c = sk.bounds.mean(0)
    # Anchors: vault (above the brow, behind the orbits) and the skull base/ear region.
    gl_y = [p[1] for p in pairs if p[0] == "glabella"][0][1]
    anchors = v[(v[:, 1] > gl_y + 10) | (v[:, 2] < c[2] - 10)]
    anchors = anchors[:: max(1, len(anchors) // 300)]
    # Condyles stay in their sockets so the jaw hinges rather than floats.
    md = trimesh.load(ANAT / "mandible.ply")
    md.apply_transform(full)
    mv = md.vertices
    condyles = [mv[(mv[:, 0] * s > 0)][(mv[(mv[:, 0] * s > 0)][:, 1]).argmax()] for s in (1, -1)]
    ctrl = np.vstack([P, anchors, condyles])
    disp = np.vstack([D, np.zeros((len(anchors) + 2, 3))])
    rbf = RBFInterpolator(ctrl, disp, kernel="gaussian", epsilon=1 / 35.0, smoothing=1e-3)
    for (name, *_), d in zip(pairs, D):
        print(f"    warp {name:16s} moves {np.linalg.norm(d):5.1f} mm  {d.round(1)}")
    FIT_INFO["face_warp"] = {p[0]: d.round(2).tolist() for p, d in zip(pairs, D)}

    def warp(points):
        points = np.asarray(points, float)
        out = points.copy()
        near = np.linalg.norm(points - P.mean(0), axis=1) < 160
        if near.any():
            out[near] = points[near] + rbf(points[near])
        return out

    return warp


def landmark_pairs(full, skin):
    """(name, bone point, goal point, axis mask): bone landmark should sit at the matching skin
    landmark minus the soft-tissue depth. Only the listed axes are constrained."""
    def load(name):
        m = trimesh.load(ANAT / f"{name}.ply")
        m.apply_transform(full)
        return m
    sk, md, th = load("skull_cranium"), load("mandible"), load("teeth")
    slab = lambda v: v[np.abs(v[:, 0]) < 3.0]
    skv, mdv, thv = slab(sk.vertices), slab(md.vertices), slab(th.vertices)
    S = skin_profile_landmarks(skin)
    Z, Y, YZ = (0, 0, 1), (0, 1, 0), (0, 1, 1)
    out = []
    # Upper face, from the bone's front profile (max z per 1 mm height band, so inner-table and
    # sinus surfaces are ignored).
    def front_at(lo, hi):
        ys = np.arange(lo, hi, 1.0)
        pts = []
        for y in ys:
            sel = skv[(np.abs(skv[:, 1] - y) < 0.75) & (skv[:, 2] > skv[:, 2].max() - 45)]
            if len(sel):
                pts.append(sel[sel[:, 2].argmax()])
        return np.array(pts)
    # Bony nasion = the frontonasal suture, i.e. the top of the nasal bones.
    nasal = trimesh.util.concatenate([load("bone_left_nasal_bone"), load("bone_right_nasal_bone")])
    na_y = nasal.vertices[:, 1].max()
    prof = front_at(na_y - 10, na_y + 45)
    na = prof[np.abs(prof[:, 1] - na_y).argmin()]
    above = prof[(prof[:, 1] > na[1] + 3) & (prof[:, 1] < na[1] + 35)]
    gl = above[above[:, 2].argmax()]
    out.append(("glabella", gl, S["glabella"] - [0, 0, FACE_TISSUE["glabella"]], Z))
    out.append(("nasion", na, S["nasion"] - [0, 0, FACE_TISSUE["nasion"]], YZ))
    # Mouth: upper incisor under the upper lip, lower incisor under the lower lip.
    ui = thv[thv[:, 2].argmax()]
    out.append(("upper_incisor", ui, S["labrale_sup"] - [0, 0, FACE_TISSUE["upper_lip"]], Z))
    out.append(("incisal_edge", ui, S["stomion"] + [0, 2, 0], Y))  # incisor tip ~2 mm above stomion
    low = thv[thv[:, 1] < ui[1] - 8]
    li = low[low[:, 2].argmax()]
    out.append(("lower_incisor", li, S["labrale_inf"] - [0, 0, FACE_TISSUE["lower_lip"]], Z))
    # Chin.
    me = mdv[mdv[:, 1].argmin()]
    out.append(("menton", me, S["menton"] + [0, FACE_TISSUE["menton"], 0], Y))
    chin = mdv[mdv[:, 1] < me[1] + 22]
    pg = chin[chin[:, 2].argmax()]
    out.append(("pogonion", pg, S["pogonion"] - [0, 0, FACE_TISSUE["pogonion"]], Z))
    fold = mdv[(mdv[:, 1] > pg[1]) & (mdv[:, 1] < li[1]) & (mdv[:, 2] > pg[2] - 20)]
    if len(fold):
        out.append(("chin_lip_fold", fold[fold[:, 2].argmin()],
                    S["labiomental_fold"] - [0, 0, FACE_TISSUE["chin_lip_fold"]], Z))
    FIT_INFO["skin_landmarks"] = {k: v.round(1).tolist() for k, v in S.items()}
    return out


def export_textures(parts=None):
    """Per-vertex UVs and base-colour textures of the bust skin and suit, for rendering."""
    parts = parts or load_bust()
    OUT.mkdir(parents=True, exist_ok=True)
    for key, name in (("HeadHires", "skin_head"), ("Don_with_skeleton:Suit3:Suittexturematerial", "suit")):
        vis = parts[key].visual
        np.save(OUT / f"{name}_uv.npy", np.asarray(vis.uv, np.float32))
        vis.material.baseColorTexture.convert("RGB").save(OUT / f"{name}_texture.png")


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
