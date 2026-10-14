"""
Build the map as one self-contained page: dist/shell-game-map.html, with
MapLibre and every GeoJSON layer inlined, so it opens from disk or as a
shared page with no server and no tile service.

    python3 shell-game/tools/build_map.py

public/geo/spots.geojson comes from score_parcels.py; until the county's
owner records are in, the map builds with no spots.
"""
import json, os

ROOT = os.path.join(os.path.dirname(__file__), "..")
GEO = os.path.join(ROOT, "public/geo")
LAYERS = ["landuse", "water", "buildings", "roads", "paths", "neighborhoods", "spots"]


def load(name):
    p = os.path.join(GEO, f"{name}.geojson")
    if not os.path.exists(p):
        return {"type": "FeatureCollection", "features": []}
    with open(p) as fh:
        return json.load(fh)


def main():
    page = open(os.path.join(ROOT, "src/map.html")).read()
    geo = json.dumps({n: load(n) for n in LAYERS}, separators=(",", ":")).replace("</", "<\\/")
    js = open(os.path.join(ROOT, "vendor/maplibre-gl.js")).read().replace("</script", "<\\/script")
    page = (page.replace("/*MAPLIBRE_CSS*/", open(os.path.join(ROOT, "vendor/maplibre-gl.css")).read())
                .replace("/*MAPLIBRE_JS*/", js)
                .replace("/*GEO*/", geo))
    os.makedirs(os.path.join(ROOT, "dist"), exist_ok=True)
    out = os.path.join(ROOT, "dist/shell-game-map.html")
    with open(out, "w") as fh:
        fh.write(page)
    print(f"wrote {out} ({os.path.getsize(out) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
