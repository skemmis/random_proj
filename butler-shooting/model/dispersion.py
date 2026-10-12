"""Shot dispersion model for the Butler shooter, built from benchmark data.

Priors come from butler-shooting/benchmark-accuracy-notes (Burcham 2018, Tikuisis 2007,
ARL-TR-7135, Kjellgren 1970, AMSAA TR-461). Each simulated "engagement" draws its own
shooter skill, stress multiplier, and volley bias, so the output impact cloud carries
our uncertainty about the shooter, not just shot-to-shot scatter.

Coordinates are in the target plane perpendicular to the line of fire, in cm, origin at
the aim point: x is the shooter's right, y is up.
"""

import numpy as np

MOA_RAD = np.pi / (180 * 60)

# Distance from muzzle to Trump's head; sources range 125-142 m (see research-notes-01).
RANGE_M = (125.0, 142.0)

PRIORS = {
    # Shot-1 random per-axis sigma for a Crooks-type shooter, stressed, deliberate.
    "sigma_shot1_moa": dict(median=3.2, log_sd=0.35),
    # Extra multiplier for follow-up shots fired 0.7-0.85 s apart (shots 2-3).
    "followup_mult": dict(median=1.5, log_sd=0.25),
    # Vertical sigma relative to horizontal (Norway SOF, Von Wahlde).
    "vert_over_horiz": (1.0, 1.25),
    # Volley bias (zero error, aim-point error), shared by shots fired without re-aiming.
    "bias_x_moa": dict(mean=0.0, sd=2.0),
    "bias_y_moa": dict(mean=0.5, sd=2.5),
}


def moa_to_cm(moa, range_m):
    return np.tan(moa * MOA_RAD) * range_m * 100.0


def sample_engagements(n, rng, priors=PRIORS):
    """Draw per-engagement shooter parameters."""
    p = priors
    sigma = p["sigma_shot1_moa"]["median"] * np.exp(rng.normal(0, p["sigma_shot1_moa"]["log_sd"], n))
    ratio = rng.uniform(*p["vert_over_horiz"], n)
    # Split so the geometric mean of the two axes equals sigma.
    sx, sy = sigma / np.sqrt(ratio), sigma * np.sqrt(ratio)
    bx = rng.normal(p["bias_x_moa"]["mean"], p["bias_x_moa"]["sd"], n)
    by = rng.normal(p["bias_y_moa"]["mean"], p["bias_y_moa"]["sd"], n)
    rng_m = rng.uniform(*RANGE_M, n)
    return dict(sx=sx, sy=sy, bx=bx, by=by, range_m=rng_m)


def sample_impacts(n, rng, aim_xy_cm=(0.0, 0.0), followup=False, priors=PRIORS):
    """Impact points (cm) in the target plane for n independent engagements."""
    e = sample_engagements(n, rng, priors)
    mult = 1.0
    if followup:
        f = priors["followup_mult"]
        mult = f["median"] * np.exp(rng.normal(0, f["log_sd"], n))
    x_moa = e["bx"] + rng.normal(0, 1, n) * e["sx"] * mult
    y_moa = e["by"] + rng.normal(0, 1, n) * e["sy"] * mult
    x = moa_to_cm(x_moa, e["range_m"]) + aim_xy_cm[0]
    y = moa_to_cm(y_moa, e["range_m"]) + aim_xy_cm[1]
    return np.column_stack([x, y]), e
