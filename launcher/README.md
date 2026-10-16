# Apollo 11 mission console

An original terminal launcher for this fork, built from scratch with Python's
standard library. It bundles four working tools in a single menu.

## Start

From the repository root:

```sh
npm start
```

Or run without Node/npm:

```sh
python3 launcher/main.py
```

Requires Python 3.10+ with the `curses` module, on macOS or Linux, and an
interactive terminal. No package installation, browser, build, or network is
required. Use at least **64 columns by 24 rows**; wider terminals show previews
beside the menu. If the window is too small, resize it to continue.

For a plain-text tool list, use `python3 launcher/main.py --list`.

## The menu

Use arrows or **J/K** to choose a tool, **Enter** to open it, or **1–4** to launch
directly. **Esc**, **B**, or **Q** returns one level; Q on the main menu exits.
The shell's terminal settings are restored when the application exits, including
on Ctrl+C. Tools do not write to the Apollo source files.

| Tool | What opens |
| --- | --- |
| Source explorer | Browse both Luminary 099 and Comanche 055, then read an original assembly listing with line numbers. |
| Command reference | Six numeric sequences with their meanings, individual keys, and links into the local assembly listing. |
| Animated scenes | Six original Arzi scenes with orbit, descent, landing, liftoff, astronauts, and a playful platform sequence. |
| Alarm laboratory | An interactive teaching model of finite core-set and VAC pools, overload, and restart recovery. |

### Source explorer

Select the Lunar Module or Command Module, then select an `.agc` file. J/K or
arrows move; Page Up/Down moves a page. Press **/** and type to filter file names;
Enter keeps the filter, while Esc clears it. An empty result is safe to navigate.

In a listing, use J/K, Page Up/Down, Home/End, and Left/Right for horizontal
panning. Esc returns to the file list. The viewer is read-only.

### Command reference

J/K or arrows selects a command. Enter opens its original Luminary source table;
Esc returns to the same card. `V` means VERB, `N` means NOUN, and `E` means ENTR.

The reference includes lamp test, P00 selection, sampled AGC time, alarm readback,
rope-memory checksum, and fresh start. It teaches the sequences; it does not send
commands to a DSKY or run the guidance software.

### Animated scenes

Choose **3** from the main menu to open the scene collection. J/K or arrows
selects an entry; Enter plays it. **1** plays the full 96-second show; **2–7**
opens an individual scene. Wider terminals show a preview beside the selection.

| Scene | What happens |
| --- | --- |
| Moon orbit | Arzi glides around a shaded, cratered Moon under gently drifting stars. |
| Powered descent | Arzi approaches Tranquility with a flickering engine plume and Earth in the sky. |
| Touchdown | A soft approach, contact, engine shutdown, and settling dust. |
| Arzi liftoff | Ignition, a dust cloud, and a climb out of the lunar view. |
| First footsteps | An astronaut sets the pole, unfurls the Lebanese flag, salutes, and returns to Arzi. |
| Moon hop | A playful astronaut jumps blocks, collects three stars, raises the Lebanese flag, and boards Arzi. |

| During playback | Action |
| --- | --- |
| Space | Pause or resume the current frame |
| R | Replay the current scene from the beginning |
| Left/Right or H/L | Play the previous/next scene individually |
| [ / ] | Seek backward/forward two seconds within the current scene, even while paused |
| Esc, B, or Q | Return to the scene picker |

The full show advances automatically, then holds on its final frame. Moon orbit
loops when played individually; the other individual scenes hold at their ending.
Pausing also freezes flames, dust, and stars. Replay is deterministic. Window
resizing redraws the same point in the scene for the new stage size.

All artwork is drawn by our terminal renderer using shaded pixel sprites and
half-block characters, which provide two vertical pixels per terminal row.
The Lebanese flag has red upper and lower bands, a white center, and a green
cedar. The astronaut sets the pole, unfurls the cloth, pauses to salute, then
returns to Arzi; the flag stays planted. Use a UTF-8 terminal font for the pixel
art. A 256-color terminal gives the full palette; basic color terminals use a
smaller palette.
Moon hop is a scripted platform animation, with the same playback controls as the
other scenes. The collection is illustrative artwork, without spacecraft physics,
actual mission timing, or AGC control.

### Alarm laboratory

| Key | Action |
| --- | --- |
| R | Toggle the added radar load |
| M | Toggle the optional monitor load |
| C | Reset the pools into a core-only example (1202) |
| V | Reset the pools into a VAC-using example (1201) |
| Space | Pause or resume |
| N | Advance one two-second cycle, including while paused |
| X | Reset the whole demonstration |
| Esc | Return to the launcher |

Try **R**, then **M**. Both loads together exceed the model's available compute.
Each unfinished cycle retains memory. In the core-only example, the eight core
sets fill; in VAC mode, the five VAC areas fill first. The next allocation raises
01202 or 01201, clears the backlog, and drops the optional monitor. The radar load
stays enabled, so you can see why shedding work restores capacity.

The historical pool sizes and alarm meanings are drawn from
[EXECUTIVE.agc](../Luminary099/EXECUTIVE.agc). **The load percentages, job behavior,
and recovery timing are deliberately simplified teaching values.** This tool is
not a CPU emulator or a historical replay. It models one resource-pressure idea;
it does not execute the original assembly. The main menu, animation, and alarm
model are independent tools.

## Checks

```sh
npm run test:launcher
```

Or `python3 -m unittest discover -s launcher -p 'test_*.py'`.
Tests cover opening and returning from every tool, source filtering and failures,
reference-to-source navigation, pause/resume, terminal sizes, path boundaries,
stable loads, both alarm/recovery paths, deterministic scene replay, full-show
transitions, seek boundaries, touchdown and settling, Lebanese flag colors and cedar, unfurling and saluting,
pixel layering, limited terminal palettes, and the platform sequence. No test dependencies are required.
