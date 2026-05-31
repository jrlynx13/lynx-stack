# Win16 NE / InstallShield trap on modern Wine

Symptom: you run an old Windows installer's `Setup.exe` under Wine
(Hangover, Winlator, Wine 9+, anything modern) and it hangs at "extracting"
forever with `winevdm.exe` pinned at 99 % CPU, OR it returns instantly with
no process spawned. The `Setup.exe` looks like a normal Windows installer.

## The actual cause

The installer is an **InstallShield 5/6 stub** from 1996-2000. These stubs
ship as **Win16 NE (New Executable)** binaries that need the **winevdm**
DOS/Win16 thunking layer. Modern Wine (9.x, 10.x, 11.x) on wow64 doesn't
support Win16 reliably — `winevdm` either spins forever trying to thunk
the calls, or it's never invoked.

You can confirm this in one second with `file`:

```bash
$ file Setup.exe
Setup.exe: MS-DOS executable, NE version 5 for MS Windows 3.10 (EXE) (GUI)
```

If you see `NE version 5 for MS Windows 3.x`, it's Win16. Same with
`_ISDel.exe` and `_Setup.dll` — InstallShield's helper EXE/DLL set is
also NE.

A modern Win32 PE installer says:

```bash
Setup.exe: PE32 executable for MS Windows
```

That one Wine handles fine.

## The fix: skip the installer

InstallShield 5/6 stubs do one job: extract a `data1.cab` archive into
`C:\Program Files\<App>\`. You can do the extract yourself with the
free `unshield` tool and skip the whole Win16 mess:

```bash
sudo apt install unshield
mkdir extracted && cd extracted
unshield x ../data1.cab
# → files spill into ./Language Independent/ etc. — find the main EXE
```

Then run the extracted main EXE directly under Wine (Win32 PE — works
fine on modern Wine):

```bash
wine PHOTOSTU.EXE
```

If the InstallShield CAB is split (`data1.cab`, `data2.cab`, …) unshield
handles the whole set automatically; point it at the directory.

## InstallShield English-folder split gotcha

Some IS5/6 builds put **English UI strings** in a separate "English"
folder from the **core DLLs** (which are language-independent). When you
launch the main EXE you get import errors like:

```
0168:err:module:loader_init Importing dlls for L"PhotoStudio.exe" failed,
status c0000135
```

The fix is to copy the missing DLLs from the language-independent folder
into the EXE's folder. The missing ones are usually generic-named C-runtime-
like or app-internal DLLs (DibPro.dll, EzDll.dll, ImgPro.dll, myCtrl.dll,
DGUI.dll, FILEFPX.dll, Brush.dll in the ArcSoft case).

## Verified

ArcSoft PhotoStudio 2000 SE (`Setup.exe` NE → unshield + direct PE launch)
runs under Hangover Wine on PRoot Ubuntu, Termux-X11 display, on a Samsung
S25 Ultra. Same workflow should apply to other late-90s/early-2000s photo
/ utility software with InstallShield 5/6 stubs.

## Sources

- Wine source: `dlls/winevdm/` and the comments in the wow64 path.
- The 99 % CPU pattern reproduced on Hangover Wine + Winlator Wine 11.0
  using identical Setup.exe input.
