"""
Turn county parcel records into Shell Game spots, each with a "how hidden"
score. Residential parcels only, and no names ever leave this script: a spot
says what the public record shows about the ownership structure (an LLC, a
Delaware formation, a registered-agent mailing address, 14 sibling homes at
the same address), never who is behind it.

    python3 shell-game/tools/score_parcels.py parcels.csv [entities.csv] \
        > shell-game/public/geo/spots.geojson

parcels.csv: one row per parcel, already mapped to the columns in PARCEL_COLS
(see shell-game/DATA.md for how the LA County assessor roll maps onto them).
entities.csv (optional): state business-registry facts per owner entity, with
the columns in ENTITY_COLS. Without it, formation state and layering are
scored as unknown, which is the honest default.

The score is a sum of points; tiers are cut from the total. Every point
comes with a plain-language reason that the map shows.
"""
import csv, json, re, sys
from collections import Counter

PARCEL_COLS = [
    "ain",            # assessor id
    "lng", "lat",     # a point inside the parcel
    "use",            # "single_family" | "condo" | "multi_family" | other (skipped)
    "units",          # dwelling units
    "owner",          # owner name as recorded (used here only, never output)
    "mail_address",   # owner mailing address, one line
    "mail_state",     # two-letter state of the mailing address
    "situs_address",  # the property's own address
    "homeowner_exemption",  # "1" if the owner claims it (lives there)
    "value",          # total assessed value, dollars
    "last_sale_price",
]
ENTITY_COLS = [
    "owner",            # as it appears on the roll, to join on
    "formed_in",        # two-letter state or country of formation
    "managers_are_entities",  # "1" if every listed manager/officer is itself a company
    "layers",           # entity hops traced before reaching a person or a dead end
    "dead_end",         # "registered_agent" | "secrecy_state" | "offshore" | "" (reached a person)
    "flags",            # "|"-separated: "offshore_leaks", "sanctions"
]

RESIDENTIAL = {"single_family", "condo", "multi_family"}

ENTITY = re.compile(
    r"\b(L\.?L\.?C|L\.?P|L\.?L\.?P|INC|INCORPORATED|CORP|CORPORATION|CO|COMPANY|LTD|LIMITED|"
    r"HOLDINGS?|PROPERT(Y|IES)|INVESTMENTS?|VENTURES?|PARTNERS(HIP)?|CAPITAL|FUND|GROUP|"
    r"REALTY|ASSETS?|ENTERPRISES?|S\.?A|B\.?V|GMBH|PTE)\b\.?"
)
TRUST = re.compile(r"\bTR(UST)?\b|\bTRS\b|\bTRUSTEES?\b")
# Revocable living trusts are how ordinary Californians avoid probate; they
# are not shells. Only trusts that look like nominees or land trusts count.
FAMILY_TRUST = re.compile(r"\b(FAMILY|LIVING|REVOCABLE|REV|SURVIVOR'?S?|BYPASS|DECEDENT'?S?)\b")

SECRECY_STATES = {"DE", "WY", "NV", "NM", "SD"}
OFFSHORE = {"VG", "KY", "PA", "BS", "BM", "JE", "GG", "IM", "SC", "MU", "LI", "BZ", "CW", "TC", "AI", "VC"}

# Mailing addresses of big registered-agent and mail-drop operators. An owner
# whose only address is one of these has told the public nothing.
AGENT_ADDRESSES = [
    r"1209 ORANGE ST",          # CT Corporation, Wilmington DE
    r"251 LITTLE FALLS DR",     # CSC, Wilmington DE
    r"2711 CENTERVILLE RD",     # CSC (older), Wilmington DE
    r"8 THE GREEN",             # Dover DE mail drop
    r"16192 COASTAL HWY",       # Harvard Business Services, Lewes DE
    r"30 N GOULD ST",           # Sheridan WY mail drop
    r"1712 PIONEER AVE",        # Cheyenne WY mail drop
    r"2710 GATEWAY OAKS DR",    # Registered agent hub, Sacramento CA
    r"330 N BRAND BLVD",        # CT Corporation, Glendale CA
    r"818 W 7TH ST",            # CT Corporation, Los Angeles CA
    r"401 RYLAND ST",           # Registered agent hub, Reno NV
    r"1802 N CARSON ST",        # Carson City NV mail drop
]
AGENT = re.compile("|".join(AGENT_ADDRESSES))
PO_BOX = re.compile(r"\bP\.?\s*O\.?\s*BOX\b|\bPMB\b|\bBOX \d+")
CARE_OF = re.compile(r"\bC/?O\b|\bATTN\b|\bLAW\b|\bLLP\b|\bCPA\b|\bACCOUNTANCY\b")


def norm(s):
    return re.sub(r"\s+", " ", (s or "").upper().replace(",", " ").replace("#", " ")).strip()


def is_entity(owner):
    o = norm(owner)
    if ENTITY.search(o):
        return "company"
    if TRUST.search(o) and not FAMILY_TRUST.search(o):
        return "trust"
    return None


def score(p, siblings, ent):
    """Points and reasons for one parcel. `siblings` counts other residential
    parcels sending tax bills to the same mailing address."""
    pts, why = 0, []

    def add(n, reason):
        nonlocal pts
        pts += n
        why.append(reason)

    kind = is_entity(p["owner"])
    if not kind:
        return 0, []
    add(1, "Owned by a company, not a person" if kind == "company" else "Owned through a trust that isn't a family trust")

    if p.get("homeowner_exemption") != "1":
        add(1, "Nobody claims it as their home")

    mail, situs = norm(p.get("mail_address")), norm(p.get("situs_address"))
    if AGENT.search(mail):
        add(3, "Tax bills go to a registered-agent office that fronts for thousands of companies")
    elif PO_BOX.search(mail):
        add(1, "Tax bills go to a PO box")
    elif CARE_OF.search(mail):
        add(1, "Tax bills go to a lawyer or accountant")
    if p.get("mail_state") and p["mail_state"].upper() != "CA":
        add(1, f"Tax bills go out of state ({p['mail_state'].upper()})")

    if siblings >= 25:
        add(3, f"{siblings} other homes send their tax bills to the same address")
    elif siblings >= 5:
        add(2, f"{siblings} other homes send their tax bills to the same address")

    if ent:
        f = (ent.get("formed_in") or "").upper()
        if f in OFFSHORE:
            add(4, "The owner was formed offshore")
        elif f in SECRECY_STATES:
            add(2, f"The owner was formed in {f}, which doesn't record who owns its companies")
        layers = int(ent.get("layers") or 0)
        if layers >= 2:
            add(min(layers, 4), f"{layers} layers of companies before the trail goes cold")
        elif ent.get("managers_are_entities") == "1":
            add(1, "Its managers are other companies")
        if ent.get("dead_end") == "registered_agent":
            add(1, "The trail ends at a registered agent")
        flags = set((ent.get("flags") or "").split("|")) - {""}
        if "offshore_leaks" in flags:
            add(5, "A name in the chain appears in the ICIJ Offshore Leaks database")
        if "sanctions" in flags:
            add(6, "A name in the chain matches a sanctions or politically-exposed-person list")

    # Sam's rule: a small local landlord with a Delaware LLC isn't the story.
    # One or two homes, a California mailing address, no layering: keep it common.
    small_local = siblings < 2 and (p.get("mail_state") or "CA").upper() == "CA" and not AGENT.search(mail)
    if small_local and pts > 3 and not (ent and int(ent.get("layers") or 0) >= 2):
        pts, why = 3, why + ["Looks like a small local landlord"]
    return pts, why


TIERS = [(12, 4, "Legendary"), (8, 3, "Rare"), (5, 2, "Uncommon"), (1, 1, "Common")]


def tier(pts):
    for floor, t, label in TIERS:
        if pts >= floor:
            return t, label
    return 0, None


def build(parcels, entities):
    homes = [p for p in parcels if p.get("use") in RESIDENTIAL]
    by_mail = Counter(norm(p.get("mail_address")) for p in homes if is_entity(p["owner"]) and p.get("mail_address"))
    ents = {norm(e["owner"]): e for e in entities}
    feats = []
    for p in homes:
        siblings = by_mail.get(norm(p.get("mail_address")), 1) - 1
        pts, why = score(p, siblings, ents.get(norm(p["owner"])))
        t, label = tier(pts)
        if not t:
            continue
        feats.append({
            "type": "Feature",
            "properties": {
                "id": p["ain"],
                "score": pts,
                "tier": t,
                "rarity": label,
                "use": p["use"],
                "units": int(float(p.get("units") or 1)),
                "value": int(float(p.get("value") or 0)),
                "why": why,
            },
            "geometry": {"type": "Point", "coordinates": [round(float(p["lng"]), 6), round(float(p["lat"]), 6)]},
        })
    return {"type": "FeatureCollection", "features": feats}


def read(path):
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


if __name__ == "__main__":
    parcels = read(sys.argv[1])
    entities = read(sys.argv[2]) if len(sys.argv) > 2 else []
    json.dump(build(parcels, entities), sys.stdout, separators=(",", ":"))
