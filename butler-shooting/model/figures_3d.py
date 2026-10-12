"""Article renders of the 3D model: likeness, x-ray cutaway, and the shooter's-eye view.

Writes PNGs into figures/. Uses the small ray-cast renderer in render.py (no GPU needed).
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import trimesh  # noqa: E402
from PIL import Image  # noqa: E402
from render import render, textured  # noqa: E402
from sim3d import Scene, fire_direction  # noqa: E402

FIG = Path(__file__).resolve().parents[1] / "figures"

SKIN = (0.93, 0.72, 0.60)
HAIR = (0.97, 0.86, 0.52)
SUIT = (0.13, 0.17, 0.33)
ANAT = {
    "bone": (0.92, 0.89, 0.80),
    "brain": (0.86, 0.50, 0.60),
    "vessel": (0.82, 0.12, 0.14),
    "airway": (0.45, 0.70, 0.80),
    "eye": (0.95, 0.95, 0.95),
}
EAR = (0.90, 0.25, 0.25)


HM = Path(__file__).resolve().parents[1] / "assets" / "head_model"


def textured_skin(scene, ear_highlight=False):
    skin = trimesh.load(HM / "skin_head.ply", process=False)
    skin.apply_transform(scene.T)
    uv = np.load(HM / "skin_head_uv.npy")
    tex = np.asarray(Image.open(HM / "skin_head_texture.png"))
    flags = np.load(HM / "skin_head_ear_flags.npy")
    tint = (flags[skin.faces].max(axis=1) == 2) if ear_highlight else None
    return skin, textured(uv, tex, tint_faces=tint)


def likeness_layers(scene, ear_highlight=False, texture=True):
    m = scene.meshes
    if texture:
        skin = [textured_skin(scene, ear_highlight)]
    else:
        skin = [(m[k], SKIN) for k in ("scalp", "face", "neck")]
        skin += [(m["ear_right"], EAR if ear_highlight else SKIN), (m["ear_left"], SKIN)]
    return skin + [(m["hair"], HAIR), (m["torso"], SUIT)]


def anatomy_layers(scene):
    m = scene.meshes
    return [(m[k], c) for k, c in ANAT.items()] + [(m["ear_right"], EAR), (m["ear_left"], SKIN)]


def xray(scene, view, up=(0, 1, 0), res=900, alpha=0.40, **kw):
    a, da = render(anatomy_layers(scene), view, up=up, res=res, **kw)
    no_hair = [(mm, c) for mm, c in likeness_layers(scene, texture=False) if mm is not scene.meshes["hair"]]
    s, ds = render(no_hair, view, up=up, res=res, **kw)
    has_s = np.isfinite(ds)
    out = a.copy()
    out[has_s] = alpha * s[has_s] + (1 - alpha) * a[has_s]
    return out


def main():
    FIG.mkdir(exist_ok=True)
    neutral = Scene(0.0)
    kw = dict(center=np.array([0, -60.0, 0]), extent=230)
    views = [((0, 0, -1), "front"), ((1, 0, 0), "right side"), ((-0.6, 0, -0.8), "front-left 3/4"),
             ((0.8, 0, -0.6), "front-right 3/4")]
    fig, ax = plt.subplots(2, 4, figsize=(20, 10.5))
    for j, (v, t) in enumerate(views):
        img, _ = render(likeness_layers(neutral), v, up=(0, 1, 0), res=700, **kw)
        ax[0, j].imshow(img)
        ax[0, j].set_title(t, fontsize=13)
        ax[1, j].imshow(xray(neutral, v, up=(0, 1, 0), res=700, **kw))
    for a in ax.ravel():
        a.axis("off")
    fig.suptitle("The model: shortlan's Sketchfab likeness (top), with BodyParts3D skull, brain, "
                 "vessels and airway fitted inside (bottom)", fontsize=14)
    fig.savefig(FIG / "model_likeness_and_xray.png", dpi=110, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    # Shooter's-eye views for a few head turns (shooter at Trump's 3 o'clock).
    rels = [90, 45, 20, 0]
    fig, ax = plt.subplots(2, len(rels), figsize=(5 * len(rels), 10.5))
    for j, rel in enumerate(rels):
        sc = Scene(90.0 - rel)
        d = fire_direction(90.0, 0.8)
        kw2 = dict(center=np.array([0, -20.0, 0]), extent=170)
        img, _ = render(likeness_layers(sc, ear_highlight=True), d, up=(0, 1, 0), res=700, **kw2)
        ax[0, j].imshow(img)
        ax[0, j].set_title(f"face turned {rel}° away from the shooter" if rel else "face toward the shooter",
                           fontsize=12)
        ax[1, j].imshow(xray(sc, d, up=(0, 1, 0), res=700, **kw2))
    for a in ax.ravel():
        a.axis("off")
    fig.suptitle("What the shooter saw, by head turn (right ear in red). The ear only sits clear of the "
                 "skull when the face is turned toward the rifle.", fontsize=14)
    fig.savefig(FIG / "shooter_view_by_head_turn.png", dpi=110, bbox_inches="tight", facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    main()
