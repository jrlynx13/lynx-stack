# ADS-B "nothing receives" on PortaPack H4M / HackRF Pro

What it looked like: open ADS-B RX app, aircraft list stays empty, no log
lines hitting `LOGS/ADSB.TXT`, even though `dump1090` on the same antenna
on a Pi5 RTL-SDR was seeing 30+ aircraft.

## The actual fixes (in order)

1. **Flash the latest Mayhem nightly** — verified working on `n_260530`
   (May 30 2026). An older nightly (~30 days back) was missing a stack of
   HackRF Pro / submodule fixes in PRs
   [#3199](https://github.com/portapack-mayhem/mayhem-firmware/pull/3199),
   [#3187](https://github.com/portapack-mayhem/mayhem-firmware/pull/3187),
   and especially
   [#3174 (HackRF submodule bump fixing EP0 transfer hangs + dropped
   SETUP packets)](https://github.com/portapack-mayhem/mayhem-firmware/pull/3174).
   See the [flash recipe](firmware-flash-FIRMWARE-dir.md).
2. **Set the gain correctly**: AMP **ON**, LNA 32 dB, VGA 24 dB, Squelch
   **0** (NOT 80). High squelch silently kills ADS-B because the 1090 MHz
   bursts are short and weak; the squelch gate cuts them before the
   decoder sees them.
3. **Confirm hardware variant matches firmware** (see
   [firmware-flash-FIRMWARE-dir.md](firmware-flash-FIRMWARE-dir.md#file-variant-matters)).

## Things you can rule out (other people's threads will say these are it)

- **Persistent-memory layout corruption** (Issue
  [#2944](https://github.com/portapack-mayhem/mayhem-firmware/issues/2944)).
  Was a real bug after PR #2934 (Jan 2026, SSB modes refactor) for users
  upgrading without clearing pmem. Fixed for clean-flash users; clearing
  pmem on the device fixes it for upgrade users. If you're on `n_260530`
  fresh-flashed, this is not your issue.
- **ADS-B database regression** (Issue
  [#2714](https://github.com/portapack-mayhem/mayhem-firmware/issues/2714)
  from June 2025, PR #2701). The `icao24.db` format change broke things
  briefly mid-2025. Fixed long since.
- **Antenna / signal**. ADS-B at 1090 MHz works fine with the stock
  PortaPack telescoping whip if the device is on / near a windowsill with
  AMP ON. If you're not seeing aircraft, the receive chain is broken,
  not the antenna.

## Confirming receive without aircraft

Open the **Spectrum** or **Microphone/Audio RX** app, tune to 1090 MHz,
span 5 MHz. If you see narrow burst spikes every few seconds → packets
in the air, decoder is the issue. If the waterfall is flat → no RF or
hardware fault, not a Mayhem bug.

## Verified

PortaPack H4M + HackRF Pro, Mayhem `n_260530`, May 31 2026.
