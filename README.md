# lynx-stack

Tips, recipes, gotchas and lessons from running unusual stacks on a single
Samsung S25 Ultra + a Pi5 cluster as the "home lab":

- **PortaPack H4M + HackRF Pro + Mayhem** — RF receive/transmit, ADS-B
- **Wine on Android** (Hangover, Winlator, xow64, Mobox) — Windows apps
- **Termux + Termux-X11 + PRoot Ubuntu** — full Linux on the phone
- **Adreno OpenCL LLM** — Qwen3-4B Q4_0 on Snapdragon 8 Elite
- **Pi5 + Hailo-10H** — ROS 2 + YOLOv8m, wheelchair brain

Most pages here exist because the official wiki / Discord answer didn't, or
because the answer that worked is buried 30 comments deep in an issue from
2020. The aim is to surface the "what actually worked" so the next person
hits the working path immediately.

## What's here

- [`portapack-mayhem/`](portapack-mayhem/) — PortaPack/Mayhem firmware, ADS-B,
  custom OSM world maps
- [`wine-on-android/`](wine-on-android/) — 4-stack compat matrix, InstallShield
  traps, Termux-X11 / Wine focus issues
- [`termux-x11/`](termux-x11/) — advanced config, window manager picks
- [`tools/`](tools/) — runnable scripts (e.g. world map builder)

Everything is best-effort, no warranty, no SLA. PRs welcome; issues welcome
but may be slow to respond.

## License

[MIT](LICENSE) for both code and docs. Use what you like; attribution
appreciated but not required.
