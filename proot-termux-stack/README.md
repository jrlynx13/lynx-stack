# PRoot Ubuntu + Termux + Android bridges

The host stack that everything else in this repo sits on top of. Samsung
S25 Ultra (Snapdragon 8 Elite, 12 GB), no root.

- **Termux** native (from F-Droid, not Play Store) — exposes Android's
  `bionic` libc, Java + Android build tools, `pkg`-installed BSD/GNU
  userland.
- **PRoot Ubuntu** (`proot-distro install ubuntu`) — proper glibc env on
  top of Termux. This is where most dev work happens (`gcc`, `python3`,
  `numpy`, `cmake`, …).
- **TermuxBridge** APK — HTTP API at `127.0.0.1:8096`, accessibility-free,
  exposes Android system calls Termux can't make as an unprivileged app:
  SAF storage access (the only reliable way to read/write USB-OTG drives
  without root), USB device access, Shizuku shell-exec.
- **Phone Bridge** APK — HTTP API at `127.0.0.1:8787`, **accessibility
  service** backed. Lets you `tap`, `swipe`, `type`, `key` against any
  app, plus a floating signal pill for live "I'm working / DONE / HELP"
  status.

## Pages

- (To come — SSH bridge from PRoot to Termux, TermuxBridge SAF workflow,
  Phone Bridge automation patterns. These are next in the writing
  queue.)
