"""Small software renderer: orthographic ray-cast shading of trimesh meshes.

No OpenGL needed. Used for checking meshes and for article figures.
"""

import numpy as np
import trimesh


def _basis(view_dir, up=(0, 0, 1)):
    d = np.asarray(view_dir, float)
    d /= np.linalg.norm(d)
    up = np.asarray(up, float)
    if abs(np.dot(up / np.linalg.norm(up), d)) > 0.99:
        up = np.array([0, 0, 1.0]) if abs(d[2]) < 0.9 else np.array([0, 1.0, 0])
    right = np.cross(d, up)
    right /= np.linalg.norm(right)
    true_up = np.cross(right, d)
    return d, right, true_up


def render(meshes, view_dir, up=(0, 0, 1), res=600, pad=0.05, extent=None, center=None,
           light=None):
    """Render a list of (mesh, rgb) pairs looking along view_dir.

    Returns an RGB float image (res x res x 3) and the per-pixel hit depth.
    extent: half-width of the square view in mesh units; default fits all meshes.
    """
    d, right, true_up = _basis(view_dir, up)
    allv = np.vstack([m.vertices for m, _ in meshes])
    if center is None:
        center = (allv.min(0) + allv.max(0)) / 2
    if extent is None:
        rel = allv - center
        extent = max(np.abs(rel @ right).max(), np.abs(rel @ true_up).max()) * (1 + pad)
    u = np.linspace(-extent, extent, res)
    uu, vv = np.meshgrid(u, -u)
    far = np.linalg.norm(allv - center, axis=1).max() * 2 + 1
    origins = center + uu.reshape(-1, 1) * right + vv.reshape(-1, 1) * true_up - d * far
    dirs = np.tile(d, (origins.shape[0], 1))
    img = np.ones((res * res, 3))
    depth = np.full(res * res, np.inf)
    if light is None:
        light = -d + 0.6 * true_up + 0.4 * right
    light = np.asarray(light, float) / np.linalg.norm(light)
    for mesh, rgb in meshes:
        locs, idx_ray, idx_tri = mesh.ray.intersects_location(origins, dirs, multiple_hits=False)
        if len(idx_ray) == 0:
            continue
        t = (locs - origins[idx_ray]) @ d
        closer = t < depth[idx_ray]
        idx_ray, idx_tri, t = idx_ray[closer], idx_tri[closer], t[closer]
        n = mesh.face_normals[idx_tri]
        n = np.where(((n @ d) > 0)[:, None], -n, n)
        lam = np.clip(n @ light, 0, 1)
        spec = np.clip(n @ (light - d) / np.linalg.norm(light - d), 0, 1) ** 30
        shade = 0.25 + 0.7 * lam
        base = rgb(mesh, idx_tri, locs[closer]) if callable(rgb) else np.asarray(rgb)[None, :]
        img[idx_ray] = np.clip(base * shade[:, None] + 0.15 * spec[:, None], 0, 1)
        depth[idx_ray] = t
    return img.reshape(res, res, 3), depth.reshape(res, res)


def textured(uv, image, tint_faces=None, tint=(0.95, 0.2, 0.2), tint_amount=0.6):
    """Colour function for render(): samples `image` (HxWx3 floats) at per-vertex `uv`."""
    image = np.asarray(image, float)
    if image.max() > 1:
        image = image / 255.0
    h, w = image.shape[:2]

    def fn(mesh, tri, locs):
        bary = trimesh.triangles.points_to_barycentric(mesh.triangles[tri], locs)
        fuv = uv[mesh.faces[tri]]
        p = np.einsum("ij,ijk->ik", bary, fuv)
        x = np.clip((p[:, 0] % 1.0) * (w - 1), 0, w - 1).astype(int)
        y = np.clip((1 - (p[:, 1] % 1.0)) * (h - 1), 0, h - 1).astype(int)
        col = image[y, x, :3]
        if tint_faces is not None:
            t = tint_faces[tri]
            col[t] = (1 - tint_amount) * col[t] + tint_amount * np.asarray(tint)
        return col

    return fn


def load_mesh(path):
    m = trimesh.load(path, force="mesh")
    return m
