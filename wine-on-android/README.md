# Wine on Android — what actually works

Run Windows software on a modern Android phone (Samsung S25 Ultra in this
case — Snapdragon 8 Elite, Adreno 830). Four parallel stacks live on this
phone for different reasons:

- **Hangover Wine on PRoot Ubuntu** — best general-purpose. Wine 11.9 +
  Box64 + FEX. Reaches Termux-X11 for display.
- **Winlator** — Wine 11.0 in an Android app, Vulkan Turnip + DXVK. Best
  for games. Hardcoded barrel-button → right-click for S-Pen.
- **xow64-wine in Termux** — Wine 10.12 staging built native against
  Termux's bionic. Useful for cutting-edge bench / single-thread tests.
- **Mobox** — Wine 9.3 Android app, Steam + Box64 preinstalled. Good
  defaults for Steam-from-Wine paths.

See:

- [4-stack compatibility matrix](compat-matrix.md)
- [The Win16 NE InstallShield trap (ArcSoft PhotoStudio 2000 SE)](win16-ne-installshield-trap.md)
