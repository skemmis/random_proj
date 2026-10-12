"""Outcome maps: what happens if a bullet crosses the target plane at (u, v).

Rather than Monte-Carlo sampling shots (noisy for a ~1% outcome), we ray-cast a dense grid of
bullet paths for a given pose, giving an exact-ish map of outcome vs impact point. Shooter
accuracy is then integrated over the map analytically: each engagement draw from the benchmark
prior is a 2D Gaussian (bias + spread), separable in u and v, so the summed density over
thousands of draws is a single matrix product.

Plane coordinates: (u, v) in mm, perpendicular to the line of fire, origin at the centre of the
cranium; u = the shooter's right, v = up (as seen by the shooter).
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from dispersion import PRIORS, moa_to_cm, sample_engagements  # noqa: E402
from sim3d import BULLET_RADIUS_MM, Scene, aim_points, classify, fire_direction, plane_basis  # noqa: E402

CODES = ["miss", "miss_hair", "ear_only_right", "ear_only_left", "minor_scalp_neck", "minor_arm",
         "brain", "vessel", "bone", "airway", "eye", "face", "torso"]
CODE = {k: i for i, k in enumerate(CODES)}
BUCKET = {"miss": "miss", "miss_hair": "miss", "ear_only_right": "ear_only", "ear_only_left": "ear_only",
          "minor_scalp_neck": "other_minor", "minor_arm": "other_minor"}
BUCKET.update({k: "killed_or_maimed" for k in ("brain", "vessel", "bone", "airway", "eye", "face", "torso")})


def grid_codes(scene, d, origin, right, up, us, vs):
    U, V = np.meshgrid(us, vs)
    pts = origin + U.reshape(-1, 1) * right + V.reshape(-1, 1) * up
    n = len(pts)
    ang = np.linspace(0, 2 * np.pi, 7)[:-1]
    offs = [np.zeros(3)] + [BULLET_RADIUS_MM * (np.cos(a) * right + np.sin(a) * up) for a in ang]
    codes = np.empty(n, np.int8)
    chunk = 60_000
    for s in range(0, n, chunk):
        p = pts[s:s + chunk]
        m = len(p)
        origins = np.concatenate([p - d * 3000.0 + o for o in offs])
        dirs = np.tile(d, (len(origins), 1))
        raw = scene.hits(origins, dirs)
        h = {g: v.reshape(7, m).any(axis=0) for g, v in raw.items()}
        lab, vk, hair_only = classify(h)
        c = np.full(m, CODE["miss"], np.int8)
        c[hair_only] = CODE["miss_hair"]
        ear_r = (lab == "ear_only") & h["ear_right"]
        c[ear_r] = CODE["ear_only_right"]
        c[(lab == "ear_only") & ~ear_r] = CODE["ear_only_left"]
        minor = lab == "other_minor"
        arm_only = minor & h["arm"] & ~(h["scalp"] | h["neck"] | h["ear_right"] | h["ear_left"])
        c[minor & ~arm_only] = CODE["minor_scalp_neck"]
        c[arm_only] = CODE["minor_arm"]
        for g in ("brain", "vessel", "bone", "airway", "eye", "face", "torso"):
            c[vk == g] = CODE[g]
        codes[s:s + chunk] = c
    return codes.reshape(len(vs), len(us))


class OutcomeMap:
    """Fine map around the head and neck plus a coarse map covering the whole upper body."""

    def __init__(self, shooter_az=90.0, head_yaw=0.0, head_pitch=0.0, head_roll=0.0, elev=0.8,
                 fine_step=1.5, coarse_step=10.0):
        self.pose = dict(shooter_az=shooter_az, head_yaw=head_yaw, head_pitch=head_pitch,
                         head_roll=head_roll, elev=elev)
        self.scene = Scene(head_yaw, head_pitch, head_roll)
        self.d = fire_direction(shooter_az, elev)
        self.right, self.up = plane_basis(self.d)
        aims = aim_points(self.scene, self.d)
        self.origin = aims["head"]
        self.aims = {k: np.array([(p - self.origin) @ self.right, (p - self.origin) @ self.up])
                     for k, p in aims.items()}
        # Fine-grid edges sit on coarse-cell edges (odd multiples of 5 mm) so the fine map
        # replaces whole coarse cells: u in [-165, 165], v in [-265, 185].
        self.fu = np.arange(-165 + fine_step / 2, 165, fine_step)
        self.fv = np.arange(-265 + fine_step / 2, 185, fine_step)
        self.cu = np.arange(-700, 700 + 1e-9, coarse_step)
        self.cv = np.arange(-1000, 300 + 1e-9, coarse_step)
        self.fine = grid_codes(self.scene, self.d, self.origin, self.right, self.up, self.fu, self.fv)
        self.coarse = grid_codes(self.scene, self.d, self.origin, self.right, self.up, self.cu, self.cv)
        self.fine_step, self.coarse_step = fine_step, coarse_step

    def probabilities(self, aim="head", n_eng=20_000, rng=None, priors=PRIORS, followup=False):
        """P(outcome code) for one shot, integrating over benchmark shooter uncertainty."""
        rng = rng or np.random.default_rng(1)
        e = sample_engagements(n_eng, rng, priors)
        mult = 1.0
        if followup:
            f = priors["followup_mult"]
            mult = f["median"] * np.exp(rng.normal(0, f["log_sd"], n_eng))
        to_mm = moa_to_cm(1.0, e["range_m"]) * 10.0  # mm per MOA for each draw
        au, av = self.aims[aim]
        mu_u, mu_v = au + e["bx"] * to_mm, av + e["by"] * to_mm
        s_u, s_v = e["sx"] * mult * to_mm, e["sy"] * mult * to_mm

        def cell_probs(us, vs, step):
            from scipy.stats import norm
            eu = np.concatenate([us - step / 2, [us[-1] + step / 2]])
            ev = np.concatenate([vs - step / 2, [vs[-1] + step / 2]])
            Pu = np.diff(norm.cdf((eu[None, :] - mu_u[:, None]) / s_u[:, None]), axis=1)
            Pv = np.diff(norm.cdf((ev[None, :] - mu_v[:, None]) / s_v[:, None]), axis=1)
            return (Pv.T @ Pu) / n_eng  # (nv, nu)

        pf = cell_probs(self.fu, self.fv, self.fine_step)
        pc = cell_probs(self.cu, self.cv, self.coarse_step)
        # Replace coarse cells covered by the fine map with the fine map's answer.
        fu0, fu1 = self.fu[0] - self.fine_step / 2, self.fu[-1] + self.fine_step / 2
        fv0, fv1 = self.fv[0] - self.fine_step / 2, self.fv[-1] + self.fine_step / 2
        inside_u = (self.cu - self.coarse_step / 2 >= fu0) & (self.cu + self.coarse_step / 2 <= fu1)
        inside_v = (self.cv - self.coarse_step / 2 >= fv0) & (self.cv + self.coarse_step / 2 <= fv1)
        covered = np.outer(inside_v, inside_u)
        out = np.zeros(len(CODES))
        np.add.at(out, self.fine.ravel(), pf.ravel())
        pc_out = pc.copy()
        pc_out[covered] = 0.0
        np.add.at(out, self.coarse.ravel(), pc_out.ravel())
        # Mass that falls outside the coarse grid is a miss.
        out[CODE["miss"]] += max(0.0, 1.0 - pc.sum())  # beyond the coarse grid
        out /= out.sum()
        return dict(zip(CODES, out))


def buckets(p):
    b = {"ear_only": 0.0, "killed_or_maimed": 0.0, "other_minor": 0.0, "miss": 0.0}
    for k, v in p.items():
        b[BUCKET[k]] += v
    return b
