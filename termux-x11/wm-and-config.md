# Termux-X11 window manager picks + the matchbox trap

If you run Wine apps under Termux-X11 with no window manager, things look
broken in subtle ways: menus won't open from clicks, dialogs appear
behind their parent windows, redraws leave stale pixels, drag doesn't
work, cursor leaves trails. The fix is to run a real window manager
inside the X session. But: **don't pick matchbox.**

## Why no WM at all breaks Wine

Wine's X11 driver (`winex11.drv`) relies on the **WM** to deliver
`WM_INITMENU` / `WM_TAKE_FOCUS` events when the user clicks the menubar.
Without a WM running, the X11 root window owns input focus and Wine's
menu HWND never sees the click as menubar activation. Same for
`Expose` events: with no WM doing window reordering, off-screen regions
that get uncovered don't get repaint requests, so Wine windows leak
stale pixels.

## Why matchbox specifically is wrong

`matchbox-window-manager` was designed for **handheld PDAs**: every
top-level window is auto-fullscreened, no decorations, no overlap.
That's hostile to Wine. Wine dialog windows get reparented into the
main window's frame; modal dialogs trap behind their owner; menus close
on focus shift because matchbox steals focus from whichever window was
last mapped.

It also doesn't honor `_NET_WM_STATE_MODAL` or `WM_TRANSIENT_FOR`
properly. Real spec-correct WMs do.

## What works: openbox + xcompmgr

```bash
# Inside PRoot Ubuntu
apt remove --purge matchbox-window-manager   # if you tried it
apt install -y openbox xcompmgr xdotool x11-utils

# Per-session, before launching Wine:
export DISPLAY=:0
openbox &                # ~4 MB RAM, ICCCM/EWMH compliant
xcompmgr -c -n &         # client-side composite, ~2 MB RAM, no shadows
sleep 0.5

wine /path/to/AppName.exe
```

Why each piece:

- **openbox** — strictest ICCCM/EWMH compliance among lightweight WMs.
  Honors `WM_TRANSIENT_FOR` and modal flags, so Wine dialog chains route
  focus correctly. No window tabs (fluxbox has those and they confuse
  Wine's owned-window hints). Per-app rules via `rc.xml` if you need
  app-specific behavior.
- **xcompmgr** — software compositor. Redirects each window into an
  offscreen pixmap and composites. Kills the stale-pixel / cursor-trail
  artifacts that show up without a compositor on minimal X servers.
  `picom` is the modern alternative but wants compositing extensions
  that Termux-X11's `lorie` server doesn't fully implement; `xcompmgr`
  is older and works against the minimal server.

## Verify the WM is doing its job

```bash
xprop -root _NET_SUPPORTING_WM_CHECK    # should print a window ID
wmctrl -l                                # list managed windows with titles
xdotool getactivewindow getwindowname   # current focus matches what you see
```

If `_NET_SUPPORTING_WM_CHECK` is empty, no WM is running. If
`getactivewindow` doesn't track what you're tapping, focus routing is
broken — recheck the Termux-X11 settings (touch mode, two-finger
gestures).

## Alternative: `wine explorer /desktop=`

If you don't want any WM at all and only need one Wine app at a time,
Wine's own virtual desktop wrapper handles the focus chain internally:

```bash
wine explorer /desktop=appname,1080x2120 /path/to/App.exe
```

Pros: zero extra processes, predictable geometry, ICCCM-immune (Wine
controls the inner WM).

Cons: locked to one virtual desktop, can't run two Wine apps side by
side, sub-windows confined to that surface, no Alt-Tab between Wine
apps.

Use this when you want a sandboxed single-app launch and don't care
about multi-window. Use openbox+xcompmgr when you want a real X session
with multiple apps.

## Termux-X11 settings that pair with the above

Open Termux-X11 preferences (gear icon) and confirm:

- **Touch mode: Touchscreen** (not Trackpad). Touchscreen mode = direct
  positional mapping, which is what paint apps and dialog clicks expect.
- **Touch-and-hold = drag: ON**. Without this, drag does nothing.
- **Two-finger gestures: ON**. Enables right-click (two-finger tap) and
  pan.
- **Stylus is touch (Wacom): ON**. S-Pen drives the cursor through the
  mouse pipeline.
- **Pinch-to-zoom: doesn't exist in Termux-X11.** Issues #669 and #597
  on the upstream repo were closed as not-planned. Use a virtual
  resolution downscale instead (see below).

## Virtual resolution as a UI-scaling lever

Termux-X11 has no internal pinch-zoom of the X server view (point above).
If you need physically larger UI elements, set Termux-X11's display
resolution to something smaller than the panel and let it upscale:

In Preferences → Output:
```
displayResolutionMode = custom
displayResolutionCustom = 720x1413     (1.5x bump)
displayFilteringMode = linear          (or nearest for crisp pixels)
```

Wine sees a 720×1413 X11 root, renders at that size, Termux-X11 upscales
to the panel. UI elements come out ~50 % larger, no zoom dance.

## Sources

- termux/termux-x11 GitHub (issues
  [#315](https://github.com/termux/termux-x11/issues/315),
  [#416](https://github.com/termux/termux-x11/issues/416),
  [#634](https://github.com/termux/termux-x11/issues/634),
  [#669](https://github.com/termux/termux-x11/issues/669),
  [#670](https://github.com/termux/termux-x11/issues/670)).
- ArchWiki [Xcompmgr](https://wiki.archlinux.org/title/Xcompmgr).
- Matchbox manpage and the
  [USENIX paper](https://www.usenix.org/legacyurl/matchbox-window-management-not-desktop)
  on its PDA-focused design intent (which is what makes it wrong for Wine).
- Verified live on Samsung S25 Ultra (Snapdragon 8 Elite, Adreno 830)
  running PRoot Ubuntu + Termux-X11 + Hangover Wine 11.9.
