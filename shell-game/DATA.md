# Data plan for spots

Research write-up with sources: `/mnt/project-files/shell-game/data-research.md` (project files).

## 1. Parcels (geometry, use, units, value)

LA County publishes its assessor parcel layer as free open data (data.lacounty.gov / public.gis.lacounty.gov), about 2.4M parcels. It has use codes, units, values and situs addresses, but **no owner names or mailing addresses**.

## 2. Owner name and mailing address

Two routes:
- **Assessor's roll** via a California Public Records Act request to LA County Assessor, Property Data Sales (quoted $64 in 2019: https://www.muckrock.com/foi/los-angeles-county-358/los-angeles-property-roll-67544/). Public record, so no license limits on a public map.
- **Resellers** with owner + mailing address already joined: Landrecords.us ($260 one-time), ReportAll USA ($400). Check their terms on publishing derived data.

## 3. Entity facts (formation state, managers, layers)

California Secretary of State (bizfileonline.sos.ca.gov): Statements of Information list an LLC's managers/officers and its jurisdiction of formation. Foreign LLCs registered in CA show their home state. Follow manager entities to count layers until a person, a registered agent, or an out-of-state entity with no public members. Delaware, Wyoming, Nevada and New Mexico disclose almost nothing past that point, which is itself a scoring signal.

Optional flags: ICIJ Offshore Leaks bulk CSV (ODbL / CC BY-SA, credit ICIJ) and OpenSanctions (CC BY-NC, fine for non-commercial) matched against entity and officer names. Names are used only for matching and never shown.

## Mapping onto score_parcels.py

`parcels.csv` columns: `ain, lng, lat, use, units, owner, mail_address, mail_state, situs_address, homeowner_exemption, value, last_sale_price`. The roll's use code maps to `use` (LA use codes starting `01` single family, `02`–`05` multi-family, `010C`/condo codes to `condo`). The roll's homeowners' exemption field maps to `homeowner_exemption`.

`entities.csv` columns: `owner, formed_in, managers_are_entities, layers, dead_end, flags`.

The registered-agent addresses in `AGENT_ADDRESSES` are a starting list from general knowledge; check them against the real roll (the most common mailing addresses among entity owners will show the actual agents).
