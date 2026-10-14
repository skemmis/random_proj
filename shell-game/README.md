# Shell Game

A satirical Pokémon-Go-style map of homes whose real owners are kept off the public record. First play area: Echo Park and Silver Lake, Los Angeles. Residential only, no names, non-commercial.

## Layout

| Path | What it is |
|---|---|
| `src/map.html` | The map page (MapLibre over our own GeoJSON, no tile service or API key). |
| `tools/build_map.py` | Inlines MapLibre and every layer into one page: `dist/shell-game-map.html`. |
| `tools/extract_basemap.py` | Rebuilds the base map from Overture Maps (adapted from Gojai's extractor). |
| `tools/fetch_parcels.py` | Downloads the play area's homes from LA County's free parcel layer into `data/parcels.csv`. |
| `tools/join_owners.py` | Fills owner name and mailing address in `data/parcels.csv` from the owner file, once there is one. |
| `data/parcels.csv` | 16,543 homes in the play area (2026 roll), owner columns blank for now. |
| `tools/score_parcels.py` | Turns parcel + entity records into spots with a "how hidden" score. |
| `public/geo/` | Base map layers (committed) and, once the data is in, `spots.geojson`. |
| `vendor/` | MapLibre GL JS 4.7.1 (BSD-3-Clause, see `vendor/LICENSE.txt`). |

## Commands

```bash
python3 -m pip install pyarrow shapely
python3 shell-game/tools/extract_basemap.py                 # base map from Overture
python3 -m unittest discover shell-game/tools                # scoring tests
python3 shell-game/tools/fetch_parcels.py                  # homes from LA County's parcel layer
python3 shell-game/tools/join_owners.py owners.csv          # once the owner file exists
python3 shell-game/tools/score_parcels.py shell-game/data/parcels.csv [entities.csv] > shell-game/public/geo/spots.geojson
python3 shell-game/tools/build_map.py                        # writes dist/shell-game-map.html
```

## Data still needed

See `DATA.md`. The free parcel layer is in; it has no owner names, so spots need the Assessor's roll (owner name + mailing address), plus California Secretary of State records for formation state and layering.
