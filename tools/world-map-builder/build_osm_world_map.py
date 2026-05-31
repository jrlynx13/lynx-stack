#!/usr/bin/env python3
"""Build a Mayhem-compatible world_map.bin from OSM raster tiles.

Format reference: ../../portapack-mayhem/world-map-bin-format.md
4-byte header (width, height as uint16 LE) + width*height pixels in RGB565 LE.

Default: 32768x32768 Web Mercator, Carto `voyager_nolabels` style, with a
higher-resolution overlay for a region you specify (default: Erie PA +/- 300mi
using zoom-10 tiles).

Streams row-by-row so peak memory stays around 50 MB even for the 32K target.

Requires: pillow, numpy. Tested on Termux (Snapdragon 8 Elite, ~10 min total).
"""
import argparse
import io
import math
import os
import struct
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None

TILE_PX = 256

# Carto rastertiles bases — see https://github.com/CartoDB/basemap-styles
TILE_BASES = {
    "voyager": "https://basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png",
    "voyager_nolabels": "https://basemaps.cartocdn.com/rastertiles/voyager_nolabels/{z}/{x}/{y}.png",
    "positron": "https://basemaps.cartocdn.com/rastertiles/positron/{z}/{x}/{y}.png",
    "positron_nolabels": "https://basemaps.cartocdn.com/rastertiles/positron_nolabels/{z}/{x}/{y}.png",
    "dark_matter": "https://basemaps.cartocdn.com/rastertiles/dark_matter/{z}/{x}/{y}.png",
}


def latlon_to_tile_xy(lat: float, lon: float, z: int) -> tuple[float, float]:
    """Web Mercator: returns fractional tile coordinates at zoom z."""
    n = 1 << z
    x = (lon + 180.0) / 360.0 * n
    lat_rad = math.radians(lat)
    y = (1 - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi) / 2 * n
    return x, y


def fetch_tile(url: str, path: str, ua: str) -> str | None:
    if os.path.exists(path) and os.path.getsize(path) > 100:
        return path
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": ua})
            with urllib.request.urlopen(req, timeout=15) as r:
                data = r.read()
            with open(path, "wb") as f:
                f.write(data)
            return path
        except urllib.error.HTTPError as e:
            if e.code in (404, 410):
                return None  # treat as a blank tile
        except Exception:
            pass
        time.sleep(0.5 * (attempt + 1))
    return None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True, help="Output world_map.bin path")
    ap.add_argument("--cache-dir", default="./tilecache",
                    help="Where downloaded tiles are kept (resumable)")
    ap.add_argument("--world-z", type=int, default=7,
                    help="Zoom level for the world basemap (z=7 → 32768x32768)")
    ap.add_argument("--style", default="voyager_nolabels",
                    choices=list(TILE_BASES),
                    help="Carto basemap style")
    ap.add_argument("--center-lat", type=float, default=None,
                    help="Region of interest center latitude (deg)")
    ap.add_argument("--center-lon", type=float, default=None,
                    help="Region of interest center longitude (deg)")
    ap.add_argument("--radius-mi", type=float, default=300.0,
                    help="Region of interest radius in miles")
    ap.add_argument("--roi-z", type=int, default=10,
                    help="Zoom level for the region-of-interest overlay")
    ap.add_argument("--workers", type=int, default=24,
                    help="Tile download concurrency")
    ap.add_argument("--ua", default="lynx-stack/world-map-builder 0.1",
                    help="HTTP User-Agent string")
    args = ap.parse_args()

    os.makedirs(args.cache_dir, exist_ok=True)

    style_url = TILE_BASES[args.style]
    world_n = 1 << args.world_z
    world_px = world_n * TILE_PX
    print(f"world: z={args.world_z} → {world_px}x{world_px} ({args.style})")

    have_roi = args.center_lat is not None and args.center_lon is not None
    if have_roi:
        # 1° lat ≈ 69 mi (constant). 1° lon ≈ 69 mi * cos(lat).
        lat_span = args.radius_mi / 69.0
        lon_span = args.radius_mi / (69.0 * math.cos(math.radians(args.center_lat)))
        n_roi = 1 << args.roi_z
        rx_w_f, ry_n_f = latlon_to_tile_xy(args.center_lat + lat_span,
                                           args.center_lon - lon_span, args.roi_z)
        rx_e_f, ry_s_f = latlon_to_tile_xy(args.center_lat - lat_span,
                                           args.center_lon + lon_span, args.roi_z)
        rx0, ry0 = int(rx_w_f), int(ry_n_f)
        rx1, ry1 = int(rx_e_f) + 1, int(ry_s_f) + 1
        roi_w = rx1 - rx0
        roi_h = ry1 - ry0
        print(f"ROI z={args.roi_z}: x[{rx0}..{rx1}] y[{ry0}..{ry1}] "
              f"= {roi_w}x{roi_h} = {roi_w * roi_h} tiles")

    # --- ROI tile download (small set first; fail-fast on auth/policy) ---
    if have_roi:
        jobs = [(args.roi_z, x, y) for y in range(ry0, ry1) for x in range(rx0, rx1)]
        print(f"ROI downloading {len(jobs)} tiles…")
        t0 = time.time()
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futs = [pool.submit(
                fetch_tile,
                style_url.format(z=z, x=x, y=y),
                os.path.join(args.cache_dir, f"{z}_{x}_{y}.png"),
                args.ua) for (z, x, y) in jobs]
            done = 0
            for _ in as_completed(futs):
                done += 1
                if done % 100 == 0:
                    print(f"  ROI {done}/{len(jobs)} ({time.time()-t0:.0f}s)")
        print(f"ROI done in {time.time()-t0:.0f}s")

    # --- world tile download ---
    jobs = [(args.world_z, x, y) for y in range(world_n) for x in range(world_n)]
    print(f"World downloading {len(jobs)} tiles…")
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs = [pool.submit(
            fetch_tile,
            style_url.format(z=z, x=x, y=y),
            os.path.join(args.cache_dir, f"{z}_{x}_{y}.png"),
            args.ua) for (z, x, y) in jobs]
        done = 0
        for _ in as_completed(futs):
            done += 1
            if done % 500 == 0:
                print(f"  world {done}/{len(jobs)} ({time.time()-t0:.0f}s)")
    print(f"World done in {time.time()-t0:.0f}s")

    # --- ROI composite (stitch + resize to its pixel footprint on the world canvas) ---
    roi_np = None
    world_x0 = world_y0 = world_x1 = world_y1 = 0
    if have_roi:
        roi_native = Image.new("RGB", (roi_w * TILE_PX, roi_h * TILE_PX), (240, 240, 240))
        for y in range(ry0, ry1):
            for x in range(rx0, rx1):
                p = os.path.join(args.cache_dir, f"{args.roi_z}_{x}_{y}.png")
                if os.path.exists(p):
                    try:
                        roi_native.paste(
                            Image.open(p).convert("RGB"),
                            ((x - rx0) * TILE_PX, (y - ry0) * TILE_PX),
                        )
                    except Exception as e:
                        print(f"  bad ROI tile {x},{y}: {e}")
        # ROI extent in world pixels: convert ROI tile-edge coords to world pixels.
        world_x0 = int(rx_w_f / n_roi * world_px)
        world_y0 = int(ry_n_f / n_roi * world_px)
        world_x1 = int(rx_e_f / n_roi * world_px) + 1
        world_y1 = int(ry_s_f / n_roi * world_px) + 1
        roi_target_w = world_x1 - world_x0
        roi_target_h = world_y1 - world_y0
        print(f"ROI → world pixels: x[{world_x0}..{world_x1}] y[{world_y0}..{world_y1}] "
              f"= {roi_target_w}x{roi_target_h}")
        roi_resized = roi_native.resize((roi_target_w, roi_target_h), Image.LANCZOS)
        roi_np = np.asarray(roi_resized, dtype=np.uint8)
        del roi_native, roi_resized

    # --- streaming row-by-row world build ---
    print(f"Writing {args.out} ({world_px}x{world_px})…")
    t0 = time.time()
    blank = Image.new("RGB", (TILE_PX, TILE_PX), (240, 240, 240))
    with open(args.out, "wb") as f:
        f.write(struct.pack("<H", world_px))
        f.write(struct.pack("<H", world_px))
        for ty in range(world_n):
            strip = Image.new("RGB", (world_px, TILE_PX))
            for tx in range(world_n):
                p = os.path.join(args.cache_dir, f"{args.world_z}_{tx}_{ty}.png")
                if os.path.exists(p):
                    try:
                        strip.paste(Image.open(p).convert("RGB"), (tx * TILE_PX, 0))
                    except Exception:
                        strip.paste(blank, (tx * TILE_PX, 0))
                else:
                    strip.paste(blank, (tx * TILE_PX, 0))
            strip_np = np.asarray(strip, dtype=np.uint8)
            # Overlay ROI if this strip intersects it
            if roi_np is not None:
                ys = ty * TILE_PX
                ye = ys + TILE_PX
                if world_y0 < ye and world_y1 > ys:
                    a = max(0, world_y0 - ys)
                    b = min(TILE_PX, world_y1 - ys)
                    sa = max(0, ys - world_y0)
                    sb = sa + (b - a)
                    strip_np = strip_np.copy()
                    strip_np[a:b, world_x0:world_x1] = roi_np[sa:sb]
            r = strip_np[:, :, 0].astype(np.uint16)
            g = strip_np[:, :, 1].astype(np.uint16)
            b_ = strip_np[:, :, 2].astype(np.uint16)
            rgb565 = ((r >> 3) << 11) | ((g >> 2) << 5) | (b_ >> 3)
            f.write(rgb565.astype("<u2").tobytes())
            if ty % 8 == 0 or ty == world_n - 1:
                print(f"  row {ty + 1}/{world_n}  {time.time() - t0:.1f}s")
    print(f"Done: {os.path.getsize(args.out):,} bytes in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
