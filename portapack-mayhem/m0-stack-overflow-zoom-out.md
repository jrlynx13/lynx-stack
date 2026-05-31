# Mayhem M0 stack overflow on extreme map zoom-out

## Symptom

In the ADS-B RX (or any GeoMap-using) app, with a full-size `world_map.bin`
(32K × 32K) loaded, zooming out a few notches past the default produces a
**Guru Meditation screen** on the PortaPack:

```
M0 Guru Meditation
Hint: Stack Overflow
r0:  0000000E
r1:  ...
...
Press DFU for Stack Dump
```

This happens on H4M + HackRF Pro running Mayhem `n_260530`. Almost certainly
happens on all builds with the unmodified GeoMap renderer.

## Cause

`firmware/application/ui/ui_geomap.cpp`, function `map_read_line_bin`,
around line 254:

```cpp
ui::Color zoom_out_buffer[(pixels * (-map_zoom))];
```

That's a **stack-allocated variable-length array**. `pixels` is the display
width (≈ 240 on H4M); `map_zoom` is a signed integer, negative for zoom-out
("collapse N source pixels into one display pixel"). At a sufficiently
negative `map_zoom`, the array's size exceeds the M0's stack budget and the
firmware panics.

This isn't specific to custom maps. The shipped 32K × 32K satellite map
hits it too if you zoom out far enough — most users just never zoom that
far on the satellite version because there's no reason to.

## Workaround for now

Don't zoom out past the level that crashes for your setup. On `n_260530`
with a 32K × 32K bin, the safe range is roughly "starting zoom" to about
3-4 notches inward.

## Fix (proposed)

Allocate the buffer on the heap (or as a fixed-size static scratch large
enough for the max zoom-out the renderer supports):

```cpp
static ui::Color zoom_out_buffer[PORTAPACK_DISPLAY_WIDTH * MAX_ZOOM_OUT];
```

…or `std::vector<ui::Color>` sized at runtime. Either avoids the stack
allocation and the crash.

I haven't filed a PR yet; planning to. If you beat me to it, please open
an issue on this repo so we don't double up.

## Sources

- Mayhem `n_260530` source (`firmware/application/ui/ui_geomap.cpp`).
- Crash reproduced live on hardware 2026-05-30, photographed.
