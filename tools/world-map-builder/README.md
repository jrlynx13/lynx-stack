# world-map-builder

Builds a Mayhem-compatible `world_map.bin` from OpenStreetMap raster tiles.

See [`portapack-mayhem/world-map-bin-format.md`](../../portapack-mayhem/world-map-bin-format.md)
for the format and why this exists.

## Use

```bash
python3 build_osm_world_map.py \
    --out world_map.bin \
    --center-lat 42.13 --center-lon -80.09 --radius-mi 300
```

Default world base = Carto `voyager_nolabels` zoom 7 (32768×32768 = 2.15 GB).
Default ROI = your given center + radius at zoom 10 — high-detail-per-pixel
overlay composited into the relevant chunk of the world canvas.

Time on Snapdragon 8 Elite (S25 Ultra):

- ROI tile download (~1k tiles): ~30 s
- World tile download (16,384 tiles): ~10 min
- Stitch + RGB565 convert: ~30 s
- Total wall clock: ~12 min for a fresh build, ~30 s if all tiles cached

## Output

Drop the resulting `world_map.bin` into `SD:/ADSB/world_map.bin` on the
PortaPack SD card. Restart the device or just re-enter the ADS-B RX app.

## Style choice

`--style voyager_nolabels` (default) is recommended for ADS-B because
the device's tiny screen makes embedded place-name text unreadable. Pass
`--style voyager` if you want labels anyway, or `--style positron_nolabels`
for a lighter palette.

## Cache behavior

Tiles land in `./tilecache/` as `{z}_{x}_{y}.png`. Re-runs hit the cache
and skip downloads. Delete the cache to force fresh tiles.

## Respecting tile providers

Default User-Agent is `lynx-stack/world-map-builder 0.1`. Be honest about
who you are if you raise concurrency or rebuild often, especially if you
switch the base URL to OSM Standard (which has a
[strict tile-usage policy](https://operations.osmfoundation.org/policies/tiles/)).
