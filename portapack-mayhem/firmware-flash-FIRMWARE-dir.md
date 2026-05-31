# Mayhem firmware flash lives in `FIRMWARE/`, not the SD card root

Verified on PortaPack H4M + HackRF Pro running Mayhem `n_260530` (May 2026).

## The trap

A lot of older howtos (including a memory note I had carried from a 2026-04-30
session) say "drop `OCI_*.ppfw.tar` on the SD card root and power on." On
current Mayhem this is **wrong** — the on-device updater scans
`<SD root>/FIRMWARE/` for `.ppfw.tar` files. Files at root are ignored.

## What actually works

```
<SD root>/
├── FIRMWARE/
│   └── OCI_hpro_mayhem_nightly_n_<date>.ppfw.tar   ← put it HERE
├── ADSB/
├── APPS/
├── SETTINGS/
└── ... (the rest of the COPY_TO_SDCARD payload)
```

1. Drop the `OCI_*.ppfw.tar` (the on-device updater, ~5.7 MB) into `FIRMWARE/`
2. Power-cycle the device
3. Splash → updater detects new firmware → flashes → boots
4. **Verify**: Settings → About → check the date string matches the file

If you put the `.ppfw.tar` at root, the device boots into whatever was
previously installed and silently ignores the file. There's no error message.

## File variant matters

Mayhem ships three variants for three different boards:

| Filename prefix | Hardware |
|---|---|
| `OCI_hackrf_…` | Original HackRF One (MAX2839 radio chip) |
| `OCI_hpro_…`   | **HackRF Pro / "praline" (MAX2831)** |
| `OCI_portarf_…`| PortaRF (different board entirely) |

If you flash `hpro` firmware onto an original HackRF, the device boots
normally (PortaPack LPC43 is fine) but **every receive app silently fails**
because the firmware drives MAX2831 register addresses on a chip that doesn't
exist. Same true the other way. ADS-B not decoding anything when the spectrum
view shows 1090 MHz bursts = a strong sign you flashed the wrong variant.

## Source

- Mayhem `README` (updater behavior) and the
  [release artifacts page](https://github.com/portapack-mayhem/mayhem-firmware/releases)
- Verified on real hardware 2026-05-30
