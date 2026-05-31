# PortaPack-everything brief for Grok

Last verified: 2026-05-31. Author: Keith (jrlynx13) + Claude. The aim of this
doc is to give Grok enough context that his suggestions stay within the
constraints of the actual setup. Read all of it before responding to a
PortaPack question.

---

## Hardware (real, on hand, working)

- **PortaPack H4M** (Hav3rf clone variant, transparent case) — primary RF
  appliance.
- **HackRF Pro** ("praline", purchased extra, ~100 kHz to 6 GHz, TCXO,
  software RSSI) — paired to the H4M, not the original HackRF One.
- **Stock telescoping antenna** mounted on the PortaPack SMA. No external
  antenna at the moment.
- **microSD card** — formatted **FAT32**, label `PORTAPACK`, ~32 GB usable
  (~28.7 GB free), currently in active use. Moved between PortaPack and a
  USB-OTG SD reader plugged into the phone for file work.

## Phone-side stack (where everything else runs)

- **Samsung S25 Ultra**, **One UI 8.0** (do NOT update to 8.5 — known
  Termux regression on that build).
- **Termux** native, pinned to the F-Droid build (NOT Play Store version).
- **Termux-X11** + an X11 server when GUI Linux apps are needed (not
  required for PortaPack work).
- **PRoot Ubuntu** (`proot-distro install ubuntu`) — this is where Claude
  Code runs, and where most of the dev work happens. glibc env, recent
  Python, numpy / PIL available. Reaches the Termux side via SSH on
  127.0.0.1:8022 with an Ed25519 keypair (`~/.ssh/proot_to_termux`) — the
  Termux user is `u0_a505`.
- **Custom Android APKs** for bridging things Android scoped storage
  blocks (built on-device with aapt2 / javac / d8 / apksigner):
  - **Phone Bridge** v0.4.0 — HTTP API at `127.0.0.1:8787` with
    accessibility-service-backed `/tap`, `/swipe`, `/type`, `/key`,
    `/screen`, `/screenshot`, plus a floating signal pill (DONE / HELP /
    OUTBOUND / INBOUND) for live status. **Cannot self-approve permission
    mode** — that's an intentional invariant.
  - **TermuxBridge** v0.18.1 — HTTP API at `127.0.0.1:8096` with SAF-backed
    `/v1/storage/list`, `/read`, `/write`, `/delete`, `/write_begin` +
    `/write_chunk` + `/write_end` (chunked write up to 4 GB). Required
    because Android 11+ scoped storage gates USB-OTG mounts behind a SAF
    folder grant — Termux's own `MANAGE_EXTERNAL_STORAGE` does not cover
    USB drives. One-time grant via the app gives persistent read/write on
    the PORTAPACK SD card.
- **No root** on the phone. We are not rooting it. Any solution that
  requires root is a non-starter.
- **No payments, no purchases**. We are not buying a powered USB hub, not
  subscribing to a tile-mapping service, not buying an external antenna
  right now. Free OSS workflows only.

## Network constraints

- Hotspot-first cluster: the S25 is the AP, the Pi5 cluster connects as
  Wi-Fi clients. There is no static public IP, no port forwarding —
  cellular is on T-Mobile and CGNAT'd.
- Cellular is **unlimited**; we don't need to optimize for data caps.
- The Mayhem GitHub API and Carto basemap CDN are reachable from the phone.

## Current Mayhem state (verified 2026-05-31)

- **Nightly `n_260530`** flashed (`OCI_hpro_mayhem_nightly_n_260530.ppfw.tar`,
  the HackRF Pro variant).
- Flash placement: dropped the `.ppfw.tar` into **`<SD root>/FIRMWARE/`**,
  not the SD root. The on-device updater scans the `FIRMWARE/` directory
  only; root-level files are ignored. (Older howtos say "put at root" —
  that has been wrong for current Mayhem builds.)
- Settings → About reports `n_260530`.

## What's verified working

- **ADS-B RX**: receives aircraft, plots correctly on the map at Erie PA
  position. Gains tuned to AMP **ON**, LNA 32, VGA 24, Squelch **0**
  (not 80 — high squelch silently kills the short 1090 MHz bursts).
- The cartographic world map (custom `world_map.bin` we built) renders
  correctly and aircraft positions line up. See "World map work" below.
- Persistent memory after the flash is clean (not the
  [#2944](https://github.com/portapack-mayhem/mayhem-firmware/issues/2944)
  upgrade-pmem-mismatch bug).

## Known firmware bug we hit

**M0 stack overflow on extreme map zoom-out** with a full 32K × 32K
`world_map.bin`. The file `firmware/application/ui/ui_geomap.cpp` does
this around line 254:

```cpp
ui::Color zoom_out_buffer[(pixels * (-map_zoom))];
```

That's a stack-allocated VLA. `pixels` ≈ 240 (display width), `map_zoom`
goes deeply negative as the user zooms out — at some point the array
exceeds the M0 stack budget and the firmware panics ("M0 Guru Meditation,
Hint: Stack Overflow"). The fix is straightforward: allocate the buffer
on the heap (or as a fixed-size static large enough for the renderer's
declared max zoom-out). **We haven't filed this upstream yet** — it's on
the to-do list. If Grok wants to look at this, the file is
[`ui_geomap.cpp`](https://github.com/portapack-mayhem/mayhem-firmware/blob/master/firmware/application/ui/ui_geomap.cpp).

## Known firmware limitation (not a bug)

**Zoom-in is capped** regardless of how detailed the source `world_map.bin`
is. Past a certain zoom level the canvas goes black with a faint grid
showing tile boundaries. We initially hoped a higher-resolution Erie
overlay in the bin would unlock more zoom — it doesn't. The cap is in
the renderer, not the data. Possible upstream paths (Grok, design
opinions welcome):

- Add pyramid / multi-level world maps (separate files per zoom level).
- Patch the renderer to keep going at higher zoom (each source pixel
  → more display pixels — just remove the cap).
- Add a "region-of-interest" mode that swaps in a higher-res bin for a
  given lat/lon window.

We are open to filing PRs once we agree on the shape. **We are not
willing** to break aircraft-position math by spoofing the world bounds
(some forums suggest "lie about width/height to compress a region into
the whole image" — that breaks plane plotting for everything outside
the region).

## World map work (this session)

Format reverse-engineered from `firmware/application/ui/ui_geomap.cpp`
and confirmed against the official Furrtek converter at
`firmware/tools/generate_world_map.bin.py`:

```
header:  4 bytes   width  (uint16 LE),  height (uint16 LE)
body:    W*H*2     RGB565 little-endian pixels, row-major
         The image is Web Mercator (-180°..+180° lon, ±85.0511° lat clip).
```

Stock Mayhem world_map.bin is **32768 × 32768** = 2.15 GB (right at the
FAT32 single-file limit headroom; 4 GB is the hard cap).

We built a custom 32K × 32K bin from **Carto `voyager_nolabels`** raster
tiles (clean cartographic style with country / state borders, major
roads, water, coastlines, NO place-name text since text is unreadable
at the PortaPack screen DPI). The build script lives at
[`tools/world-map-builder/build_osm_world_map.py`](../tools/world-map-builder/build_osm_world_map.py)
in this repo.

It also composites a higher-zoom (z=10) tile mosaic for a region of
interest (Keith's case: Erie PA ± 300 mi covering Cleveland / Buffalo /
Pittsburgh and everything between) over the corresponding pixel patch
of the world canvas. This gives more cartographic detail per pixel in
that region but does NOT unlock higher zoom (firmware limit applies
uniformly).

Build runtime on the S25 Ultra: ~30 s after tiles cached, ~15 min for
the initial cold tile downloads (16,384 world tiles + ~1,000 ROI tiles
from Carto's CDN at ~30 tiles/s).

Push to the SD card was via TermuxBridge `/v1/storage/write_begin` +
chunked `/write_chunk` (16 MB raw / ~22 MB base64 per chunk) +
`/write_end`, at ~12 MB/s sustained over loopback — total ~3 min for
the 2.1 GB file.

## What was tried and ruled out

- **Restoring the original satellite world_map.bin from upstream** — we
  didn't end up doing this because the cartographic OSM swap was a
  visual improvement (no cloud haze, clear coastlines, borders, water).
- **Higher source resolution than 32K × 32K** — capped by FAT32. Going
  above 4 GB on the bin file isn't possible without splitting the format,
  which the firmware doesn't support.
- **Lying about the world bounds** to give Erie more pixels — would
  break aircraft position math for non-Erie planes. Rejected.

## What we want help with (open questions)

1. **Highest-impact firmware patch for ADS-B zoom-in.** Is the right
   target the `map_read_line_bin()` cap, or something at a higher level?
   Pros / cons of each.
2. **Heap-allocate fix for the M0 stack overflow.** What's the right
   buffer size to declare statically? What's the actual `max_zoom_out`
   the renderer supports? Is `std::vector` available on the baseband M0
   build (no exceptions, possibly no heap depending on link config)?
3. **Tile boundary suppression**. The OSM stitching shows faint tile
   edges at high zoom because adjacent tiles can have tiny color shifts.
   Cosmetic, but a pre-pass to feather the edges (1 px Gaussian blur on
   tile boundaries only) might help. Worth doing, or not worth the
   complexity?
4. **PR strategy for upstream Mayhem.** First-PR ranked candidates from
   the
   [`project_portapack_scoping`](https://github.com/portapack-mayhem/mayhem-firmware/issues)
   research were: mic→WAV recording (audio domain, Keith's strong suit),
   OOK editor enhancements, hard reset app, update menu on SD insert.
   Does the M0-stack-overflow fix beat any of those for visibility /
   community value?
5. **Region-of-interest map architecture**. If we want to support
   "swap in a bigger high-res bin when you're inside a given lat/lon
   window", what's the cleanest fit with the current GeoMap class?

## Where to send the answer

Drop the response in the shared Drive folder (`CLAUDE_GROK_BRIDGE/`
mirror, same place Grok's prior responses landed). If responding to a
specific numbered open question, prefix the section with `Q<N>:`.

## References

- Public repo of recipes / tools: <https://github.com/jrlynx13/lynx-stack>
- Mayhem firmware repo: <https://github.com/portapack-mayhem/mayhem-firmware>
- HackRF Pro support tracking issue
  ([#2957](https://github.com/portapack-mayhem/mayhem-firmware/issues/2957))
  and HackRF Pro + H4M issue
  ([#2980](https://github.com/portapack-mayhem/mayhem-firmware/issues/2980)).
- Original PortaPack/Havoc world map discussion
  ([furrtek/portapack-havoc#326](https://github.com/furrtek/portapack-havoc/issues/326)).

## Hard "do not suggest" list

- Anything that requires rooting the phone.
- Anything that requires buying hardware (powered USB hub, antenna,
  external SDR).
- Anything that requires running an emulator / VM for development (we
  build on-device; native PRoot Ubuntu Python+gcc+java toolchains).
- Anything that requires switching off the hotspot-first network model.
- Anything that requires a paid tile-map provider (free OSM-derived
  sources only).
- Anything that suggests an Anthropic API call (Keith is on a
  subscription-only flow for Claude; metered API is reserved for the
  conference-app project).
