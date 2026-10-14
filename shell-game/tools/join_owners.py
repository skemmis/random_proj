"""
Fill the owner columns of data/parcels.csv from an owner-name file, once one
exists: the Assessor's roll from a Public Records Act request, or a reseller
extract (Landrecords.us, ReportAll USA, ...). Rows join on AIN.

    python3 shell-game/tools/join_owners.py owners.csv [--map owner=OWNER_NAME ...]

Column names differ by source, so each target column is looked up from a list
of known spellings (ALIASES, case- and punctuation-insensitive); --map
overrides any of them. A mailing address split over several columns (house
number, street, unit, city/state, zip) is glued back into one line, and the
mail state is taken from its own column or parsed off the end of the address.

After joining, it prints the mailing addresses most shared by company owners
(addresses only, never names), which is how to check AGENT_ADDRESSES in
score_parcels.py against the real roll.
"""
import argparse, csv, os, re, sys
from collections import Counter

sys.path.insert(0, os.path.dirname(__file__))
from score_parcels import PARCEL_COLS, RESIDENTIAL, is_entity, norm

ROOT = os.path.join(os.path.dirname(__file__), "..")
PARCELS = os.path.join(ROOT, "data/parcels.csv")

ALIASES = {
    "ain": ["ain", "apn", "parcelnumber", "parcelid", "parcel", "pin", "assessorid"],
    "owner": ["owner", "ownername", "owner1", "firstownername", "firstowner", "ownernm", "owner1name", "name1"],
    "mail_address": ["mailaddress", "mailingaddress", "mailadd", "mailaddr", "mailaddress1", "mailingaddress1", "mailfulladdress"],
    "mail_house": ["mailaddresshouseno", "mailhouseno", "mailhousenumber", "mailnumber"],
    "mail_street": ["mailaddressstreetname", "mailstreet", "mailstreetname"],
    "mail_unit": ["mailaddressunit", "mailunit", "mailaddress2"],
    "mail_city": ["mailaddresscityandstate", "mailcity", "mailingcity", "mailcitystate"],
    "mail_state": ["mailstate", "mailingstate", "mailstate2", "mailst"],
    "mail_zip": ["mailaddresszip", "mailzip", "mailingzip", "mailzipcode"],
    "last_sale_price": ["lastsaleprice", "saleprice", "lastsaleamount", "saleamount", "recentsaleamount", "salesprice"],
}
STATE_AT_END = re.compile(r"\b([A-Z]{2})\b\s*(\d{5}(-\d{4})?)?\s*$")


def key(name):
    return re.sub(r"[^a-z0-9]", "", name.lower())


def ain(s):
    """AINs print as 5077-001-001 or 5077001001; compare as bare digits."""
    return re.sub(r"\D", "", s or "")


def resolve(header, overrides):
    have = {key(h): h for h in header}
    cols = {}
    for target, names in ALIASES.items():
        if target in overrides:
            cols[target] = overrides[target]
            continue
        cols[target] = next((have[n] for n in names if n in have), None)
    if not cols["ain"] or not cols["owner"]:
        sys.exit(f"can't find the AIN and owner columns in {header}; pass --map ain=... owner=...")
    return cols


def owner_row(r, cols):
    get = lambda t: (r.get(cols[t]) or "").strip() if cols.get(t) else ""
    if get("mail_address"):
        mail = " ".join(x for x in [get("mail_address"), get("mail_city"), get("mail_zip")] if x)
    else:
        mail = " ".join(x for x in [get("mail_house"), get("mail_street"), get("mail_unit"), get("mail_city"), get("mail_zip")] if x)
    mail = norm(mail)
    state = get("mail_state").upper()[:2]
    if not state:
        m = STATE_AT_END.search(mail)
        state = m.group(1) if m else ""
    price = re.sub(r"[^\d.]", "", get("last_sale_price"))
    return {"owner": get("owner"), "mail_address": mail, "mail_state": state, "last_sale_price": price}


def join(parcels, owners, cols):
    by_ain = {ain(r[cols["ain"]]): owner_row(r, cols) for r in owners}
    hit = 0
    for p in parcels:
        o = by_ain.get(ain(p["ain"]))
        if o:
            p.update({k: v for k, v in o.items() if v})
            hit += 1
    return hit


def shared_addresses(parcels, n=25):
    c = Counter(p["mail_address"] for p in parcels
                if p.get("use") in RESIDENTIAL and p.get("mail_address") and is_entity(p.get("owner")))
    return c.most_common(n)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("owners")
    ap.add_argument("--parcels", default=PARCELS)
    ap.add_argument("--map", nargs="*", default=[], help="target=SourceColumn overrides")
    args = ap.parse_args()
    overrides = dict(m.split("=", 1) for m in args.map)

    with open(args.parcels, newline="") as fh:
        parcels = list(csv.DictReader(fh))
    with open(args.owners, newline="", encoding="utf-8-sig", errors="replace") as fh:
        rd = csv.DictReader(fh)
        cols = resolve(rd.fieldnames, overrides)
        hit = join(parcels, rd, cols)
    with open(args.parcels, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=PARCEL_COLS)
        w.writeheader()
        w.writerows(parcels)

    print(f"columns used: { {k: v for k, v in cols.items() if v} }", file=sys.stderr)
    print(f"owner found for {hit} of {len(parcels)} homes", file=sys.stderr)
    print("most shared company mailing addresses (check against AGENT_ADDRESSES):", file=sys.stderr)
    for addr, count in shared_addresses(parcels):
        print(f"  {count:5d}  {addr}", file=sys.stderr)


if __name__ == "__main__":
    main()
