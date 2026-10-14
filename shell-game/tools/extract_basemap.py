"""
One-time extraction of the base map for the first play area (Echo Park and
Silver Lake, Los Angeles). Outputs are committed to public/geo, so the map
never calls a tile service at runtime. Adapted from Gojai's
tools/map/extract_overture.py: the source is Overture Maps (OSM-derived,
ODbL/CDLA) read straight from its public S3 bucket.

    python3 -m pip install pyarrow shapely
    python3 shell-game/tools/extract_basemap.py            # all layers
    python3 shell-game/tools/extract_basemap.py roads      # one layer
"""
import json, os, sys, time
from urllib.parse import urlparse

import pyarrow.compute as pc
import pyarrow.dataset as ds
import pyarrow.fs as pfs
import shapely
from shapely.geometry import box, mapping

RELEASE = "2026-09-23.1"
ROOT = f"overturemaps-us-west-2/release/{RELEASE}"
OUT = os.path.join(os.path.dirname(__file__), "../public/geo")

# Echo Park and Silver Lake, from Dodger Stadium's edge west to Hyperion and
# from the 101 north to the reservoir. Keep in sync with BBOX in src/area.ts.
BBOX = (-118.2850, 34.0640, -118.2440, 34.1050)
# Streets, parks and water reach further out so a wide screen never shows
# the map's edge; building footprints stay inside BBOX to keep the page small.
CONTEXT = (-118.3300, 34.0450, -118.2000, 34.1250)
CLIP = box(*CONTEXT)
CORE = box(*BBOX)


def s3():
    kw = {}
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    if proxy:
        p = urlparse(proxy)
        kw["proxy_options"] = {"scheme": p.scheme or "http", "host": p.hostname, "port": p.port}
    return pfs.S3FileSystem(anonymous=True, region="us-west-2", **kw)


FS = s3()


def query(theme, typ, cols):
    t = time.time()
    d = ds.dataset(f"{ROOT}/theme={theme}/type={typ}", filesystem=FS, format="parquet")
    b = lambda k: pc.field("bbox", k)
    x0, y0, x1, y1 = BBOX if theme == "buildings" else CONTEXT
    f = (b("xmax") > x0) & (b("xmin") < x1) & (b("ymax") > y0) & (b("ymin") < y1)
    rows = d.to_table(columns=cols + ["geometry"], filter=f).to_pylist()
    print(f"{theme}/{typ}: {len(rows)} rows in {time.time() - t:.0f}s")
    return rows


def name(r):
    return ((r.get("names") or {}).get("primary")) or ""


def geom(r, simplify=0.0, clip=CLIP):
    g = shapely.from_wkb(r["geometry"])
    if clip is not None:
        g = g.intersection(clip)
    if simplify:
        g = g.simplify(simplify, preserve_topology=True)
    return None if g.is_empty else shapely.set_precision(g, 1e-5)  # ~1 m


def write(fname, features):
    p = os.path.join(OUT, fname)
    with open(p, "w") as fh:
        json.dump({"type": "FeatureCollection", "features": features}, fh, separators=(",", ":"))
    print(f"wrote {p} ({os.path.getsize(p) / 1024:.0f} KB, {len(features)} features)")


def feature(g, props):
    return {"type": "Feature", "properties": props, "geometry": mapping(g)}


# Road class → render tier t (3 freeway/arterial … 0 lane).
ROAD_TIERS = {
    "motorway": 3, "trunk": 3, "primary": 3, "secondary": 2, "tertiary": 2,
    "residential": 1, "unclassified": 1, "living_street": 1, "unknown": 1, "service": 0,
}
TRAIL_CLASSES = {"path", "footway", "cycleway", "bridleway", "track", "steps", "pedestrian"}


def roads():
    feats, paths = [], []
    for r in query("transportation", "segment", ["names", "subtype", "class"]):
        if r["subtype"] != "road":
            continue
        g = geom(r)
        if g is None:
            continue
        n, c = name(r), r["class"]
        if c in TRAIL_CLASSES:
            # Silver Lake's public stairways are part of the neighborhood's walking map.
            if c in {"steps", "path", "footway", "pedestrian"} and n:
                paths.append(feature(g, {"name": n, "c": c}))
        elif c in ROAD_TIERS and (c != "service" or n):
            feats.append(feature(g, {"name": n, "t": ROAD_TIERS[c]}))
    write("roads.geojson", feats)
    write("paths.geojson", paths)


WATER = {"stream", "river", "canal", "lake", "pond", "reservoir", "water"}


def water():
    feats = []
    for r in query("base", "water", ["names", "subtype", "class"]):
        if r["subtype"] not in WATER:
            continue
        g = geom(r, 0.00001)
        if g is not None:
            feats.append(feature(g, {"name": name(r), "c": r["subtype"]}))
    write("water.geojson", feats)


LANDUSE = {"park", "golf", "protected", "education", "cemetery", "religious", "recreation"}


def landuse():
    feats = []
    for r in query("base", "land_use", ["names", "subtype", "class"]):
        s = r["subtype"]
        if s not in LANDUSE:
            continue
        g = geom(r, 0.00001)
        if g is not None and g.geom_type in ("Polygon", "MultiPolygon"):
            feats.append(feature(g, {"name": name(r), "c": s}))
    write("landuse.geojson", feats)


# Building classes that mean somebody lives there. Overture leaves most LA
# buildings unclassified, so "unknown" is drawn as a plain footprint.
HOMES = {"house", "residential", "apartments", "detached", "semidetached_house", "terrace", "bungalow", "dormitory"}


def buildings():
    feats = []
    for r in query("buildings", "building", ["class", "subtype"]):
        g = geom(r, 0.000005, CORE)
        if g is None or g.geom_type not in ("Polygon", "MultiPolygon"):
            continue
        g = shapely.set_precision(g, 1e-5)  # ~1 m; keeps 26k footprints small
        if g.is_empty:
            continue
        home = r["class"] in HOMES or r["subtype"] == "residential"
        feats.append(feature(g, {"h": 1 if home else 0}))
    write("buildings.geojson", feats)


def neighborhoods():
    """Neighborhood names as label points (Overture divisions). Overture has
    few LA neighborhood polygons, so the map labels them instead of outlining."""
    feats = []
    for r in query("divisions", "division", ["names", "subtype"]):
        if r["subtype"] not in ("neighborhood", "macrohood", "microhood"):
            continue
        g = geom(r, clip=CORE)
        if g is not None and g.geom_type == "Point":
            feats.append(feature(g, {"name": name(r), "rank": {"macrohood": 2, "microhood": 1}.get(r["subtype"], 0)}))
    write("neighborhoods.geojson", feats)


TASKS = {"roads": roads, "water": water, "landuse": landuse, "buildings": buildings, "neighborhoods": neighborhoods}

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for t in sys.argv[1:] or TASKS:
        TASKS[t]()
