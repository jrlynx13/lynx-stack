# Mayhem `world_map.bin` format and a builder

The Mayhem ADS-B / GeoMap app loads a single binary file
(`SD:/ADSB/world_map.bin`) as the world basemap. Format is simple but
mostly undocumented outside the C++ source.

## Format

```
offset  bytes   meaning
   0      2     width  (uint16, little-endian)
   2      2     height (uint16, little-endian)
   4      W*H*2 pixels (RGB565 little-endian, row-major)
```

Each pixel is packed as `RRRRRGGGGGGBBBBB` from a 24-bit RGB source:

```python
pixel = ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)
struct.pack('<H', pixel)
```

The source image **must already be in Web Mercator** projection
(±85.0511287798066° latitude clip) spanning −180° to +180° longitude.
The firmware uses `lon_to_pixel_x_tile()` / `lat_to_pixel_y_tile()`
(Web Mercator inverse) to plot aircraft positions; no projection metadata
is stored in the file.

## Constraints

- **Max single-file size on FAT32 = 4 GB** → max ~46340 × 46340 square
  pixels. Mayhem's shipped `world_map.bin` is **32768 × 32768** (= 2.15 GB,
  ≈ standard Web Mercator square at ±85.05° clip).
- 32K × 32K is currently the practical max because of FAT32, not because
  of any firmware limit. Going wider/taller is fine until 4 GB.

## Building a custom map from OSM tiles

Script: [`tools/world-map-builder/build_osm_world_map.py`](../tools/world-map-builder/build_osm_world_map.py).

What it does:

1. Downloads 16,384 tiles at zoom 7 from a Carto rastertiles endpoint
   (`voyager_nolabels` by default — no place-name text, just borders /
   roads / water / coastlines).
2. Optionally downloads higher-zoom tiles for a region of interest
   (default: Erie PA ± 300 mi, z=10) and composites them over the
   base for higher-detail-per-pixel in your region.
3. Stitches row-by-row → RGB565 → writes the bin. Stream-based so peak
   memory stays under ~50 MB for the 32K × 32K output.

On a Snapdragon 8 Elite (S25 Ultra) it runs in ~15 minutes wall-clock
including tile downloads.

```bash
python3 tools/world-map-builder/build_osm_world_map.py \
    --out world_map.bin \
    --center-lat 42.13 --center-lon -80.09 --radius-mi 300
```

Drop the result into `SD:/ADSB/world_map.bin` (replacing the upstream
satellite-imagery version that ships with Mayhem). Restart the device or
just re-enter the ADS-B RX app.

## Tile source choice matters

- **`voyager_nolabels`** (recommended): clean cartographic style with
  country/state borders, major roads, water, coastlines. NO place name
  text (text is unreadable at PortaPack resolution anyway).
- `voyager` (with labels): same style but city / town names become illegible
  gray smudges at the device's effective DPI.
- `positron`: lighter, less colorful — possibly better readability but less
  feature contrast.
- OpenStreetMap Standard tile server: works, but please throttle / set
  a User-Agent per their
  [tile usage policy](https://operations.osmfoundation.org/policies/tiles/).

## Known firmware limitations (NOT data problems)

1. **Zoom-in cap**: past a certain zoom you get a black canvas. Higher source
   resolution doesn't help — it's a firmware-side rendering cap.
2. **M0 stack overflow on extreme zoom-out** when the map is full-size 32K
   × 32K. See [m0-stack-overflow-zoom-out.md](m0-stack-overflow-zoom-out.md).
3. The faint grid lines visible at high zoom = OSM tile boundaries from
   the stitching. Cosmetic; less visible with seamless tile sources.

## Sources

- `firmware/application/ui/ui_geomap.cpp` (the file reader) and
  `firmware/tools/generate_world_map.bin.py` (the official simple
  JPG → bin converter from Furrtek's original) in the
  [mayhem-firmware repo](https://github.com/portapack-mayhem/mayhem-firmware).
- Verified on H4M + HackRF Pro running `n_260530`, May 31 2026.
