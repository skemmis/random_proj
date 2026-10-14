"""
Download LA County's free assessor parcel records for the play area and write
the file the rest of the pipeline reads:

    data/parcels.csv   residential parcels in score_parcels.py's PARCEL_COLS,
                       owner columns blank until the owner-name file arrives
                       (join_owners.py fills them)

    python3 shell-game/tools/fetch_parcels.py [--raw data/raw/parcels.geojson]

Source: LA County Assessor parcels on the county's public GIS server
(public.gis.lacounty.gov, LACounty_Parcel MapServer layer 0). Free and open,
about 2.4M parcels countywide; it carries use, units, assessed values,
situs address and the homeowners' exemption, but no owner names.
"""
import argparse, csv, json, os, sys, time, urllib.parse, urllib.request

sys.path.insert(0, os.path.dirname(__file__))
from score_parcels import PARCEL_COLS

ROOT = os.path.join(os.path.dirname(__file__), "..")
# Echo Park + Silver Lake. Keep in sync with BBOX in extract_basemap.py.
BBOX = (-118.2850, 34.0640, -118.2440, 34.1050)
SERVICE = "https://public.gis.lacounty.gov/public/rest/services/LACounty_Cache/LACounty_Parcel/MapServer/0/query"
FIELDS = [
    "AIN", "UseType", "UseCode", "UseDescription", "Units1", "Units2", "Units3", "Units4", "Units5",
    "SitusFullAddress", "Roll_Year", "Roll_LandValue", "Roll_ImpValue", "Roll_HomeOwnersExemp",
    "CENTER_LAT", "CENTER_LON",
]
PAGE = 1000  # the server's maxRecordCount


def use_of(code):
    """LA County use codes: 01xx single family (4th character C, D or E marks
    a condo unit), 02-05 two to five-plus units. A trailing V is vacant land,
    and commercial, industrial and government codes are out of scope."""
    code = (code or "").strip().upper()
    if code.endswith("V"):
        return None
    if code.startswith("01"):
        return "condo" if len(code) == 4 and code[3] in "CDE" else "single_family"
    if code[:2] in ("02", "03", "04", "05"):
        return "multi_family"
    return None


def fetch(bbox):
    env = {"xmin": bbox[0], "ymin": bbox[1], "xmax": bbox[2], "ymax": bbox[3], "spatialReference": {"wkid": 4326}}
    feats, offset = [], 0
    while True:
        q = {
            "geometry": json.dumps(env), "geometryType": "esriGeometryEnvelope", "inSR": 4326,
            "spatialRel": "esriSpatialRelIntersects", "where": "1=1", "outFields": ",".join(FIELDS),
            "returnGeometry": "false", "orderByFields": "OBJECTID",
            "resultOffset": offset, "resultRecordCount": PAGE, "f": "json",
        }
        url = SERVICE + "?" + urllib.parse.urlencode(q)
        for attempt in range(4):
            try:
                with urllib.request.urlopen(url, timeout=120) as r:
                    page = json.load(r)
                break
            except Exception as e:
                if attempt == 3:
                    raise
                print(f"retrying page at {offset}: {e}", file=sys.stderr)
                time.sleep(2 ** (attempt + 1))
        if "error" in page:
            raise RuntimeError(page["error"])
        got = page.get("features", [])
        feats += [{"properties": g["attributes"]} for g in got]
        print(f"{len(feats)} parcels", file=sys.stderr)
        if len(got) < PAGE:
            return {"type": "FeatureCollection", "features": feats}
        offset += PAGE


def rows(fc):
    seen = set()
    for f in fc["features"]:
        a = f["properties"]
        use = use_of(a.get("UseCode"))
        if not use or a["AIN"] in seen or a.get("CENTER_LAT") is None:
            continue
        if not any(a.get(f"Units{i}") for i in range(1, 6)) and not a.get("Roll_ImpValue"):
            continue  # no building on the roll
        seen.add(a["AIN"])
        units = sum(a.get(f"Units{i}") or 0 for i in range(1, 6)) or 1
        yield {
            "ain": a["AIN"],
            "lng": a["CENTER_LON"], "lat": a["CENTER_LAT"],
            "use": use, "units": units,
            "owner": "", "mail_address": "", "mail_state": "",
            "situs_address": a.get("SitusFullAddress") or "",
            "homeowner_exemption": "1" if (a.get("Roll_HomeOwnersExemp") or 0) > 0 else "0",
            "value": (a.get("Roll_LandValue") or 0) + (a.get("Roll_ImpValue") or 0),
            "last_sale_price": "",
        }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", help="reuse (or save) the raw download at this path")
    args = ap.parse_args()
    if args.raw and os.path.exists(args.raw):
        fc = json.load(open(args.raw))
    else:
        fc = fetch(BBOX)
        if args.raw:
            os.makedirs(os.path.dirname(args.raw) or ".", exist_ok=True)
            json.dump(fc, open(args.raw, "w"))

    out_csv = os.path.join(ROOT, "data/parcels.csv")
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    with open(out_csv, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=PARCEL_COLS)
        w.writeheader()
        n = 0
        for row in rows(fc):
            w.writerow(row)
            n += 1
    print(f"{len(fc['features'])} parcels downloaded, {n} homes -> {os.path.normpath(out_csv)}", file=sys.stderr)


if __name__ == "__main__":
    main()
