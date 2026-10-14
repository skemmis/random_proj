# Data plan for spots

Research write-up with sources: `/mnt/project-files/shell-game/data-research.md` (project files).

## 1. Parcels (geometry, use, units, value)

LA County publishes its assessor parcel layer as free open data (data.lacounty.gov / public.gis.lacounty.gov), about 2.4M parcels. It has use codes, units, values, situs addresses and the homeowners' exemption, but **no owner names or mailing addresses**.

**Done (2026-10-14).** `tools/fetch_parcels.py` pulls the play area from the county's `LACounty_Parcel` MapServer (layer 0, 2026 roll) and writes `data/parcels.csv` in `PARCEL_COLS`, owner columns blank. Of 18,879 parcels in the bbox, 16,543 are homes: 8,587 single family, 1,556 condo units, 6,400 two-to-five-plus-unit buildings (46,025 units). Vacant land (use codes ending `V`) and parcels with no building on the roll are dropped.

No homeowners' exemption claimed: 53% of single-family homes, 65% of condos, 76% of multi-unit buildings. That alone means "rented or second home", not "shell"; it only becomes a signal next to a company owner.

## 2. Owner name and mailing address

Waiting on Sam's pick of route. When the file arrives:

```bash
python3 shell-game/tools/join_owners.py owners.csv     # fills owner, mail_address, mail_state, last_sale_price
python3 shell-game/tools/score_parcels.py shell-game/data/parcels.csv > shell-game/public/geo/spots.geojson
python3 shell-game/tools/build_map.py
```

`join_owners.py` joins on AIN (dashes ignored), recognizes the roll's and the resellers' usual column names, takes `--map target=Column` for anything else, and prints the company mailing addresses shared by the most homes so `AGENT_ADDRESSES` can be checked. The owner file stays out of the repo; only the scored spots (no names) get committed.

Two routes:
- **Assessor's roll** via a California Public Records Act request to LA County Assessor, Property Data Sales (quoted $64 in 2019: https://www.muckrock.com/foi/los-angeles-county-358/los-angeles-property-roll-67544/). Public record, so no license limits on a public map.
- **Resellers** with owner + mailing address already joined: Landrecords.us ($260 one-time), ReportAll USA ($400). Check their terms on publishing derived data.

## 3. Entity facts (formation state, managers, layers)

California Secretary of State (bizfileonline.sos.ca.gov): Statements of Information list an LLC's managers/officers and its jurisdiction of formation. Foreign LLCs registered in CA show their home state. Follow manager entities to count layers until a person, a registered agent, or an out-of-state entity with no public members. Delaware, Wyoming, Nevada and New Mexico disclose almost nothing past that point, which is itself a scoring signal.

Optional flags: ICIJ Offshore Leaks bulk CSV (ODbL / CC BY-SA, credit ICIJ) and OpenSanctions (CC BY-NC, fine for non-commercial) matched against entity and officer names. Names are used only for matching and never shown.

## Mapping onto score_parcels.py

`parcels.csv` columns: `ain, lng, lat, use, units, owner, mail_address, mail_state, situs_address, homeowner_exemption, value, last_sale_price`. Use code maps to `use` (`01xx` single family, 4th character `C`/`D`/`E` condo, `02`–`05` multi-family); `Roll_HomeOwnersExemp > 0` maps to `homeowner_exemption`; value is land plus improvements. `fetch_parcels.py` already does this from the free layer.

`entities.csv` columns: `owner, formed_in, managers_are_entities, layers, dead_end, flags`.

The registered-agent addresses in `AGENT_ADDRESSES` are a starting list from general knowledge; check them against the real roll (the most common mailing addresses among entity owners will show the actual agents).
