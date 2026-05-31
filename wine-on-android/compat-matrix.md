# Wine on Android: 4-stack compatibility matrix

Four Wine stacks live on the same Samsung S25 Ultra for different purposes.
This is the quick-reference matrix for picking which one to point at a
given Windows app.

| Stack                          | Where it runs                     | Wine    | Display       |
| ------------------------------ | --------------------------------- | ------- | ------------- |
| **Hangover / PRoot Ubuntu**    | PRoot Ubuntu glibc env            | 11.9    | Termux-X11    |
| **Winlator**                   | Android app, own embedded container | 11.0    | own surface   |
| **xow64-wine in Termux**       | Termux native (bionic)            | 10.12 staging | Termux-X11 |
| **Mobox**                      | Android app, Steam+Box64 prebaked | 9.3     | own surface   |

## Quick decision tree

1. Run `file <app>.exe`.
2. Output starts `MS-DOS executable, NE …` → **Win16**, see
   [Win16 NE InstallShield trap](win16-ne-installshield-trap.md). None
   of the four stacks reliably runs Win16 NE — you have to extract the
   payload and run the underlying PE directly.
3. Output starts `PE32 executable for MS Windows` → modern Wine OK.
   Pick a stack by app type:
   - **Productivity / GDI / utility apps** (text editors, photo apps,
     legacy CAD): **Hangover / PRoot** is the smoothest because you get
     proper X11 + WM + xdotool scripting (see
     [termux-x11/wm-and-config.md](../termux-x11/wm-and-config.md)).
   - **Games with DirectX or Vulkan**: **Winlator**. It ships DXVK +
     Vulkan-Turnip + ESYNC/FSYNC support and has the most aggressive
     compatibility surface for game-engine wrappers.
   - **Anything that needs S-Pen barrel-button right-click**: **Winlator**
     is the only stack that wires the stylus barrel button to mouse
     button 3. Termux-X11 doesn't (upstream issue #315 closed open).
   - **Steam-based games or apps with Steam DRM**: **Mobox** has Steam
     preinstalled with working Box64 hooks. Save the setup time.
   - **Cutting-edge staging features / single-thread perf experiments**:
     **xow64-wine** ships staging branches (currently 10.12) and runs
     native to Termux (no PRoot overhead). Useful for benchmarking but
     less polished than Hangover for daily use.

## Per-app-class compatibility summary

| App class                                | Hangover/PRoot | Winlator | xow64 | Mobox |
| ---------------------------------------- | -------------- | -------- | ----- | ----- |
| Win16 NE (Windows 3.x, IS5/6 stubs)      | ❌ no winevdm  | ❌       | ❌    | ❌    |
| Win32 PE 9x/XP-era (MFC42, GDI+ basic)   | ✅              | ✅        | ⚠ staging| ✅     |
| Win32 PE Win7/10-era (.NET 4.x)          | ✅ (needs `vcrun*` + `dotnet4*`) | ✅ | ⚠ | ⚠ |
| WPF (.NET 3.0+ XAML)                     | ❌ Wine-Mono gap | ❌      | ❌    | ❌    |
| DirectX 9 games                          | ⚠ no DXVK by default | ✅      | ⚠     | ✅     |
| DirectX 10/11 games                      | ⚠ via DXVK    | ✅        | ⚠     | ✅     |
| DirectX 12 games                         | ❌ Adreno Turnip gap | ⚠ pre-2022 | ❌  | ⚠ pre-2022 |
| 16-bit DOS (.exe via DOSBox)             | ❌ install DOSBox separately | ❌ | ❌ | ❌ |
| Java Web Start (legacy)                  | ⚠ via OpenJDK | ⚠         | ❌    | ⚠     |
| Steam client itself                      | ⚠ heavy        | ✅ wineprefix | ❌  | ✅ first-class |
| Wintab pressure (Krita / Painter)        | ❌ Termux-X11 has no XI2 pressure | ❌ | ❌ | ❌ |
| Print preview / print spool              | ❌              | ❌        | ❌    | ❌    |

Legend: ✅ works, ⚠ partial / needs setup, ❌ known-broken.

## Per-stack quick notes

### Hangover / PRoot Ubuntu
- Best Wine version (11.9) and best general scripting integration
  (xdotool + a real WM).
- No DXVK by default — install separately if you need it, or use
  Winlator for games.
- Display: Termux-X11 with openbox + xcompmgr (see
  [termux-x11/wm-and-config.md](../termux-x11/wm-and-config.md)).
- Env that helps: `WINEDLLOVERRIDES="mscoree,mshtml=d;winemenubuilder.exe=d"`,
  `WINEDEBUG=-all`.

### Winlator
- Container-based, polished UI.
- DXVK + Turnip Vulkan baked in.
- **S-Pen barrel button = right-click** is hardcoded in
  `MainActivity.onTouchEvent` — the only stack that does this.
- Touchpad cursor mode (taps don't click at tap coords, they click at
  where the floating cursor is). Trips up the Phone Bridge if you try
  to drive Winlator UI from accessibility taps.

### xow64-wine
- Native to Termux bionic. No PRoot, less overhead.
- Staging-branch features (10.12 as of mid-2026).
- Less battle-tested on actual app compat; treat as a perf/experimental
  stack, not the daily driver.

### Mobox
- App with Steam preinstalled. Box64 hooks already set up.
- Good for getting a working game running in 10 minutes.
- Less control over Wine prefix internals than Hangover/PRoot.

## Cross-cutting limitations

- **All four**: no Wintab pressure passthrough on Termux-X11; the upstream
  driver advertises pressure valuators but never emits XI_Motion samples.
  Paint apps that need pressure (Krita, Painter, Clip Studio under Wine)
  draw constant width.
- **All four**: no print spool to Android printer. If you need to print,
  save the document and use an Android print app.
- **All four**: WPF apps are broken. Wine-Mono doesn't ship a working WPF
  implementation as of mid-2026.

## Sources

- WineHQ AppDB (per-app entries).
- Live cross-testing on the actual hardware (S25 Ultra, ArcSoft
  PhotoStudio 2000 SE as the Win32 PE test case).
- Winlator `MainActivity.java` source for the S-Pen wiring.
- termux/termux-x11 issues #315, #634 for the XI2 pressure / barrel
  button gaps.
