# Apollo 11 mission console

An original terminal launcher for this fork, built from scratch with Python's
standard library. It bundles five working tools in a single menu.

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

Use arrows or **J/K** to choose a tool, **Enter** to open it, or **1–5** to launch
directly. **Esc**, **B**, or **Q** returns one level; Q on the main menu exits.
The shell's terminal settings are restored when the application exits, including
on Ctrl+C. Tools do not write to the Apollo source files.

| Tool | What opens |
| --- | --- |
| Source explorer | Browse both Luminary 099 and Comanche 055, then read an original assembly listing with line numbers. |
| Command reference | Six numeric sequences with their meanings, individual keys, and links into the local assembly listing. |
| Animated scenes | Six original Arzi scenes with orbit, descent, landing, liftoff, astronauts, and a playful platform sequence. |
| Alarm laboratory | An interactive teaching model of finite core-set and VAC pools, overload, and restart recovery. |
| DSKY computer panel | A green guidance-computer display, keypad, verb/noun entry, warning lights, and scripted Arzi descent readings. |

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

### DSKY computer panel

Choose **5** from the main menu. The panel includes PROG, VERB, NOUN, three signed
readouts, a keypad, and eleven annunciators. A terminal with at least 32 rows
shows large segmented digits; shorter terminals show compact values. Wider
terminals also show flight cards and descent progress. Press **?** to see all
commands at any terminal size.
Type command cards directly, with or without spaces. After using the arrows to
focus a keypad button, Space presses that button instead.

Start with `V35 E` to test the lights. Then type `V37 E 63 E` to start a
90-second scripted descent. The panel selects V16 N60 automatically: horizontal
speed in feet/second, vertical rate in feet/second, and altitude in feet.
It advances through P63 braking, P64 approach, P66 final descent, and contact.
At T+35 seconds, a scripted 01202 overload lights PROG and holds the descent;
press **P** (PRO) to acknowledge it and continue. The pause for acknowledgment
is part of this teaching scenario, not historical restart behavior.

| Command | Action in this panel |
| --- | --- |
| V35 E | Illuminate every lamp and display segment for five seconds |
| V37 E 63 E | Start or replay the descent |
| V16 N60 E | Monitor horizontal speed, altitude rate, and altitude |
| V16 N63 E | Monitor total speed, altitude rate, and altitude |
| V16 N65 E | Monitor the panel's hours, minutes, and seconds |
| V06 N60 E | Hold a snapshot while the descent continues |
| V05 N09 E | Show the three alarm-code registers in octal, newest first |
| V37 E 00 E | Select idle and stop the descent at its current readings |
| V36 E | Fresh start: clear the scenario, alarm history, entries, and clock |

The noun meanings and units follow the local
[Luminary verb/noun table](../Luminary099/ASSEMBLY_AND_OPERATION_INFORMATION.agc).
**The telemetry, 90-second timeline, program transitions, and overload event
are invented teaching values.** This panel does not execute AGC instructions or
control the animated-scene collection.

| Keyboard | Panel action |
| --- | --- |
| V / N | Select VERB / NOUN entry |
| 0–9 | Enter a digit; verb, noun, and program entries require two digits |
| E or Enter | ENTR: commit the entry and execute the supported command |
| C / Backspace | CLR: clear the current entry / delete one digit |
| K | KEY REL: cancel the current entry |
| R | RSET: clear OPR ERR and the RESTART indicator |
| P | PRO: acknowledge the scripted descent alarm |
| Arrows, then Space | Focus a keypad button, then press it |
| T / ] | Pause or resume / advance five seconds, including while paused |
| ? / Esc | Open or close command help / close help or return to the launcher |

Unsupported commands and incomplete entries illuminate OPR ERR and leave the
active telemetry intact. Use CLR or Backspace to correct an entry, or KEY REL
to cancel it. RSET clears OPR ERR; PRO acknowledges a descent alarm. The +/−
buttons report that signed register loading is unavailable; the registers are
read-only. N65 measures time spent in this panel, including standby and alarm
holds; T freezes it. Returning to the launcher freezes the panel until reopened.

## Checks

```sh
npm run test:launcher
```

Or `python3 -m unittest discover -s launcher -p 'test_*.py'`.
Tests cover opening and returning from every tool, source filtering and failures,
reference-to-source navigation, pause/resume, terminal sizes, path boundaries,
stable loads, both alarm/recovery paths, deterministic scene replay, full-show
transitions, seek boundaries, touchdown and settling, Lebanese flag colors and cedar, unfurling and saluting,
pixel layering, limited terminal palettes, and the platform sequence. DSKY checks
cover entry/correction/cancellation, lamp tests, live monitoring versus snapshots,
alarm acknowledgment and readback, idle and fresh start, clock rollover, keypad
navigation, help, resizing, and invalid commands. No test dependencies are required.
