#!/usr/bin/env python3
"""Apollo 11 terminal launcher. Python 3.10+, macOS or Linux; no packages needed."""

import argparse
import curses
import sys
import textwrap
import time

from core import AlarmDemo, CATALOG, COMMANDS, MODULES, read_source, source_files

from scenes import PIXEL_COLORS, SCENES, ScenePlayer, render_scene


class Launcher:
    def __init__(self, screen):
        self.screen = screen
        self.view = "menu"
        self.menu_index = self.module_index = self.file_index = self.manual_index = 0
        self.files = []
        self.query = ""
        self.searching = False
        self.lines = []
        self.source_name = ""
        self.source_parent = "files"
        self.scroll = self.column = 0
        self.scene_index = 0
        self.player = ScenePlayer()
        self.paused = False
        self.demo = AlarmDemo()
        self.status = ""
        self.alive = True
        self.started = time.monotonic()
        self.styles = dict.fromkeys(["normal", "dim", "accent", "cyan", "selected", "error"], 0)
        self.color_enabled = False
        self.color_pairs = {}
        self.next_color_pair = 1
        self.counts = {name: len(source_files(name)) for name, _ in MODULES}

    def run(self):
        try:
            curses.curs_set(0)
        except curses.error:
            pass
        self.screen.keypad(True)
        self.screen.timeout(33)
        if hasattr(curses, "set_escdelay"):
            curses.set_escdelay(25)
        if curses.has_colors():
            curses.start_color()
            colors = [252, 244, 214, 81, 234, 203] if curses.COLORS >= 256 else [7, 7, 3, 6, 0, 1]
            background = 234 if curses.COLORS >= 256 else 0
            for number, (name, foreground) in enumerate(zip(self.styles, colors), 1):
                curses.init_pair(number, foreground, colors[2] if name == "selected" else background)
                self.styles[name] = curses.color_pair(number)
                self.color_pairs[(foreground, colors[2] if name == "selected" else background)] = self.styles[name]
            self.next_color_pair = len(self.styles) + 1
            self.color_enabled = True
            self.screen.bkgd(" ", self.styles["normal"])
        last = time.monotonic()
        while self.alive:
            now = time.monotonic()
            self.tick(min(now - last, 0.15))
            last = now
            self.draw()
            try:
                key = self.screen.get_wch()
            except curses.error:
                continue
            self.handle_key(key)

    def tick(self, seconds):
        if self.paused:
            return
        if self.view == "scene":
            self.player.advance(seconds)
        elif self.view == "alarms":
            self.demo.advance(seconds)

    def text(self, y, x, value, style="normal", width=None):
        height, columns = self.screen.getmaxyx()
        if y < 0 or y >= height or x < 0 or x >= columns - 1:
            return
        available = columns - x - 1 if width is None else min(width, columns - x - 1)
        value = "".join(char if char.isprintable() else " " for char in str(value).expandtabs(4))
        try:
            self.screen.addnstr(y, x, value, max(0, available), self.color(style))
        except curses.error:
            pass  # A terminal can resize between measuring it and drawing.

    def color(self, style):
        if style in self.styles:
            return self.styles[style]
        if not self.color_enabled or not style.startswith("pixel:"):
            return self.styles["normal"]
        top, bottom = style.split(":")[1:]
        palette = 0 if curses.COLORS >= 256 else 1
        pair = (PIXEL_COLORS[top][palette], PIXEL_COLORS[bottom][palette])
        if pair not in self.color_pairs:
            if self.next_color_pair >= curses.COLOR_PAIRS:
                return self.styles["normal"]
            curses.init_pair(self.next_color_pair, *pair)
            self.color_pairs[pair] = curses.color_pair(self.next_color_pair)
            self.next_color_pair += 1
        self.styles[style] = self.color_pairs[pair]
        return self.styles[style]

    def paragraph(self, y, x, value, width, style="dim"):
        for offset, line in enumerate(textwrap.wrap(value, max(1, width))):
            self.text(y + offset, x, line, style, width)

    def footer(self, help_text):
        height, width = self.screen.getmaxyx()
        self.text(height - 3, 3, "-" * (width - 6), "dim")
        self.text(height - 2, 3, help_text, "cyan")

    def draw(self):
        self.screen.erase()
        height, width = self.screen.getmaxyx()
        if height < 24 or width < 64:
            self.text(1, 1, "APOLLO 11", "accent")
            self.text(3, 1, "Resize to at least 64 columns x 24 rows.")
            self.text(5, 1, f"Current: {width} x {height}.  Q quits from the menu.", "dim")
            self.screen.refresh()
            return
        self.text(1, 3, "A P O L L O  /  1 1", "accent")
        elapsed = int(time.monotonic() - self.started)
        self.text(1, width - 24, f"SESSION {elapsed // 60:02}:{elapsed % 60:02}", "dim")
        titles = {"menu": "MISSION CONSOLE", "sources": "SOURCE EXPLORER / SELECT MODULE", "files": "SOURCE EXPLORER / SELECT FILE", "reader": self.source_name, "manual": "FLIGHT MANUAL / COMMAND REFERENCE", "scenes": "ARZI / ANIMATED SCENES", "scene": f"ARZI / {self.player.scene.title.upper()}", "alarms": "ALARM LABORATORY"}
        self.text(3, 3, titles[self.view], "cyan")
        if self.status:
            self.text(4, 3, self.status, "error")
        getattr(self, f"draw_{self.view}")()
        self.screen.refresh()

    def draw_menu(self):
        _, width = self.screen.getmaxyx()
        left_width = width // 2 - 7 if width >= 100 else width - 8
        self.text(5, 3, "Choose your next mission.", "dim")
        for i, (_, title, description) in enumerate(CATALOG):
            y = 7 + i * 3
            style = "selected" if i == self.menu_index else "normal"
            self.text(y, 3, f" {'>' if i == self.menu_index else ' '} [{i + 1}] {title} ".ljust(left_width), style, left_width)
            self.paragraph(y + 1, 10, description, left_width - 7)
        self.text(20, 3, "Original tools for this fork. Built with Python's standard library.", "dim")
        if width >= 100:
            x = width // 2 + 3
            self.text(7, x, "YOUR NEXT STOP", "accent")
            previews = (
                ["COMANCHE 055 / COLUMBIA", f"{self.counts['Comanche055']} original assembly files", "", "LUMINARY 099 / ARZI", f"{self.counts['Luminary099']} original assembly files"],
                ["VERB     NOUN", " 16       65", "", "V = action    N = data    E = enter", "Read the code. Open the original listing."],
                ["SHADED PIXEL ART", "6 SCENES / ONE FULL SHOW", "", "Orbit. Land. Liftoff.", "First footsteps. Moon hop.", "", "Lebanese flag / green cedar"],
                ["CORE SETS  [#.......]  1 / 8", "VAC AREAS  [.....]     0 / 5", "", "1201 / no VAC areas", "1202 / no core sets", "", "An illustrative teaching model."],
            )
            for i, line in enumerate(previews[self.menu_index]):
                self.text(9 + i, x, line, "dim")
        self.footer("J/K or arrows select   ENTER open   1-4 launch   Q quit")

    def draw_sources(self):
        for i, (name, description) in enumerate(MODULES):
            self.text(7 + i * 4, 3, f" > {name}  /  {description} ", "selected" if i == self.module_index else "normal")
            self.text(8 + i * 4, 6, f"{self.counts[name]} original .agc files / read-only", "dim")
        self.footer("UP/DOWN or J/K select   ENTER browse   ESC back")

    def visible_files(self):
        return [name for name in self.files if self.query.lower() in name.lower()]

    def draw_files(self):
        height, width = self.screen.getmaxyx()
        files = self.visible_files()
        self.text(5, 3, f"{MODULES[self.module_index][0]}   {len(files)} files   Filter: {self.query or '(none)'}", "accent")
        rows = height - 11
        start = max(0, self.file_index - rows + 1)
        for i, name in enumerate(files[start:start + rows], start):
            self.text(7 + i - start, 3, f" {'>' if i == self.file_index else ' '} {name} ".ljust(width - 7), "selected" if i == self.file_index else "normal")
        if not files:
            self.text(8, 3, "No matching assembly files. Press / to change the filter.", "dim")
        self.footer("Type to filter / ENTER finish / ESC clear" if self.searching else "J/K move  PGUP/DN page  / filter  ENTER read  ESC back")

    def draw_reader(self):
        height, width = self.screen.getmaxyx()
        self.text(5, 3, f"LINE {self.scroll + 1} / {len(self.lines)}    COLUMN {self.column + 1}    READ-ONLY", "accent")
        for i, line in enumerate(self.lines[self.scroll:self.scroll + height - 10]):
            self.text(7 + i, 3, f"{self.scroll + i + 1:5} ", "dim", 6)
            self.text(7 + i, 10, line.expandtabs(4)[self.column:], "dim" if line.lstrip().startswith("#") else "normal", width - 13)
        self.footer("J/K scroll  PGUP/DN  LEFT/RIGHT pan  HOME/END  ESC back")

    def draw_manual(self):
        _, width = self.screen.getmaxyx()
        code, title, keys, description, filename, line = COMMANDS[self.manual_index]
        self.text(5, 3, "Reference only. Commands are not executed here.", "dim")
        if width >= 100:
            for i, (sequence, label, *_) in enumerate(COMMANDS):
                self.text(7 + i * 2, 3, f" {sequence:<13} {label} ".ljust(43), "selected" if i == self.manual_index else "normal", 43)
            x, y, card_width = 49, 7, width - 53
        else:
            x, y, card_width = 3, 7, width - 7
            self.text(y, x, f"COMMAND {self.manual_index + 1} / {len(COMMANDS)}  -  UP/DOWN to browse", "dim")
            y += 2
        self.text(y, x, code, "accent")
        self.text(y + 2, x, title)
        self.text(y + 4, x, keys, "cyan")
        self.paragraph(y + 6, x, description, card_width)
        self.text(y + 10, x, f"Luminary 099 / source line {line}", "dim")
        self.footer("J/K choose  ENTER read original source  ESC back")

    def draw_scenes(self):
        height, width = self.screen.getmaxyx()
        titles = ["Play the full show"] + [scene.title for scene in SCENES]
        preview = SCENES[max(0, self.scene_index - 1)]
        description = "All six scenes, from Moon orbit to one small hop." if self.scene_index == 0 else preview.description
        self.text(5, 3, description, "dim")
        left_width = width // 2 - 7 if width >= 100 else width - 7
        for i, title in enumerate(titles):
            duration = sum(scene.duration for scene in SCENES) if i == 0 else SCENES[i - 1].duration
            label = f" {'>' if i == self.scene_index else ' '} [{i + 1}] {title:<24} {duration:.0f}s "
            self.text(7 + i * 2, 3, label.ljust(left_width), "selected" if i == self.scene_index else "normal", left_width)
        if width >= 100:
            x = width // 2 + 3
            self.text(7, x, "PREVIEW / " + preview.title.upper(), "accent")
            frame, _ = render_scene(max(0, self.scene_index - 1), preview.duration * 0.35, width - x - 4, height - 14)
            for sx, sy, text, style in frame.runs():
                self.text(9 + sy, x + sx, text, style)
        self.footer("J/K select   ENTER play   1-7 launch   ESC back")

    def draw_scene(self):
        height, width = self.screen.getmaxyx()
        frame, caption = render_scene(self.player.index, self.player.elapsed, width - 6, height - 12)
        self.text(5, 3, caption, "cyan")
        for x, y, text, style in frame.runs():
            self.text(7 + y, 3 + x, text, style)
        state = "PAUSED" if self.paused else "COMPLETE" if self.player.finished else "PLAYING"
        mode = "SHOW" if self.player.play_all else "SOLO"
        self.text(height - 5, 3, f"{self.player.index + 1}/6  {mode}  {self.player.elapsed:04.1f}/{self.player.scene.duration:.0f}s  {state}", "accent")
        size = min(44, width - 8)
        filled = round(self.player.elapsed / self.player.scene.duration * size)
        self.text(height - 4, 3, "[" + "#" * filled + "." * (size - filled) + "]", "dim")
        self.footer("SPACE pause  R replay  LEFT/RIGHT scene  [/] seek  ESC back")

    def draw_alarms(self):
        height, width = self.screen.getmaxyx()
        demo = self.demo
        self.text(5, 3, "ILLUSTRATIVE MODEL / load values are not flight telemetry", "dim")
        self.text(7, 3, f"RADAR {'ON ' if demo.radar else 'OFF'}     MONITOR {'ON ' if demo.monitor else 'OFF'}     {'PAUSED' if self.paused else 'RUNNING'}", "cyan")
        self.text(9, 3, f"DEMAND  {demo.demand:.0%} / {'OVERLOAD' if demo.demand > 1 else 'WITHIN CAPACITY'}", "error" if demo.demand > 1 else "accent")
        bar_width = min(width - 24, 55)
        filled = int(min(demo.demand, 1) * bar_width)
        self.text(10, 3, "[" + "#" * filled + "." * (bar_width - filled) + "]", "accent")
        self.text(12, 3, f"CORE SETS  [{'#' * demo.cores}{'.' * (8 - demo.cores)}]  {demo.cores} / 8")
        self.text(13, 3, f"VAC AREAS  [{'#' * demo.vacs}{'.' * (5 - demo.vacs)}]     {demo.vacs} / 5")
        self.text(15, 3, f"LAST ALARM {demo.last_alarm}    RESTARTS {demo.restarts}    T+ {demo.elapsed:05.1f}s", "accent")
        self.text(16, 3, f"POOL: {'VAC + core sets / 1201' if demo.vac_mode else 'core-only jobs / 1202'}", "dim")
        self.paragraph(18, 3, demo.message, width - 7)
        if height >= 28:
            self.paragraph(21, 3, "Try R then M. Each unfinished two-second cycle retains memory. Exhaustion restarts the model, clears the backlog, and drops the monitor.", width - 7)
        self.footer("R radar M monitor C/V pool SPACE pause N +2s X reset ESC")

    def open(self, destination):
        self.view = destination
        self.paused = False
        self.status = ""
        if destination == "alarms":
            self.demo = AlarmDemo()

    def open_source(self, module, filename, line=1, parent="files"):
        try:
            lines = read_source(module, filename)
        except (OSError, ValueError) as error:
            self.status = f"Cannot open source: {error}"
            return
        self.lines = lines
        self.source_name = f"{module}/{filename}"
        self.scroll = max(0, min(line - 1, len(lines) - 1))
        self.column = 0
        self.source_parent = parent
        self.view = "reader"
        self.status = ""

    def back(self):
        self.status = ""
        if self.view == "reader":
            self.view = self.source_parent
        elif self.view == "files":
            self.view = "sources"
        elif self.view == "scene":
            self.view = "scenes"
        else:
            self.view = "menu"

    def handle_key(self, key):
        if self.searching:
            if key == "\x1b":
                self.query, self.searching = "", False
            elif key in ("\n", "\r", curses.KEY_ENTER):
                self.searching = False
            elif key in (curses.KEY_BACKSPACE, "\x7f", "\b"):
                self.query = self.query[:-1]
            elif isinstance(key, str) and key.isprintable():
                self.query += key
            self.file_index = 0
            return
        if isinstance(key, str):
            key = key.lower()
        if key in ("q", "Q", "\x1b", "b"):
            if self.view == "menu":
                self.alive = False
            else:
                self.back()
            return
        down = key in ("j", curses.KEY_DOWN)
        up = key in ("k", curses.KEY_UP)
        enter = key in ("\n", "\r", curses.KEY_ENTER)
        delta = int(down) - int(up)
        if self.view == "menu":
            self.menu_index = (self.menu_index + delta) % len(CATALOG)
            if isinstance(key, str) and key in "1234":
                self.menu_index = int(key) - 1
                enter = True
            if enter:
                self.open(CATALOG[self.menu_index][0])
        elif self.view == "scenes":
            self.scene_index = (self.scene_index + delta) % (len(SCENES) + 1)
            if isinstance(key, str) and key in "1234567":
                self.scene_index = int(key) - 1
                enter = True
            if enter:
                self.player.select(max(0, self.scene_index - 1), play_all=self.scene_index == 0)
                self.open("scene")
        elif self.view == "sources":
            self.module_index = (self.module_index + delta) % len(MODULES)
            if enter:
                self.files = source_files(MODULES[self.module_index][0])
                self.file_index, self.query, self.view = 0, "", "files"
        elif self.view == "files":
            files = self.visible_files()
            page = max(1, self.screen.getmaxyx()[0] - 11)
            delta += page * ((key == curses.KEY_NPAGE) - (key == curses.KEY_PPAGE))
            self.file_index = max(0, min(self.file_index + delta, len(files) - 1))
            if key == "/":
                self.searching = True
            if enter and files:
                self.open_source(MODULES[self.module_index][0], files[self.file_index])
        elif self.view == "reader":
            page = max(1, self.screen.getmaxyx()[0] - 10)
            delta += page * ((key == curses.KEY_NPAGE) - (key == curses.KEY_PPAGE))
            if key == curses.KEY_HOME:
                self.scroll = 0
            elif key == curses.KEY_END:
                self.scroll = max(0, len(self.lines) - page)
            else:
                self.scroll = max(0, min(self.scroll + delta, len(self.lines) - 1))
            self.column = max(0, self.column + 8 * ((key == curses.KEY_RIGHT) - (key == curses.KEY_LEFT)))
        elif self.view == "manual":
            self.manual_index = (self.manual_index + delta) % len(COMMANDS)
            if enter:
                _, _, _, _, filename, line = COMMANDS[self.manual_index]
                self.open_source("Luminary099", filename, line, "manual")
        elif self.view in ("scene", "alarms"):
            if key == " ":
                self.paused = not self.paused
            if self.view == "scene":
                if key == "r":
                    self.player.elapsed = 0
                elif key in (curses.KEY_LEFT, curses.KEY_UP, "h", "k"):
                    self.player.select((self.player.index - 1) % len(SCENES))
                elif key in (curses.KEY_RIGHT, curses.KEY_DOWN, "l", "j"):
                    self.player.select((self.player.index + 1) % len(SCENES))
                elif key in ("[", "]"):
                    self.player.seek(2 if key == "]" else -2)
            elif self.view == "alarms":
                if key in ("r", "R"):
                    self.demo.radar = not self.demo.radar
                elif key in ("m", "M"):
                    self.demo.monitor = not self.demo.monitor
                elif key in ("c", "C", "v", "V"):
                    self.demo.select_pool(key in ("v", "V"))
                elif key in ("n", "N"):
                    self.demo.advance(2)
                elif key in ("x", "X"):
                    self.demo = AlarmDemo()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="Print the available tools without entering the TUI")
    args = parser.parse_args()
    if args.list:
        for i, (_, title, description) in enumerate(CATALOG, 1):
            print(f"{i}. {title}: {description}")
        return 0
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        print("Open an interactive terminal and run: npm start\nUse --list to list the Apollo tools.", file=sys.stderr)
        return 1
    try:
        curses.wrapper(lambda screen: Launcher(screen).run())
    except KeyboardInterrupt:
        return 130
    except curses.error as error:
        print(f"Could not start the terminal display: {error}", file=sys.stderr)
        return 1
    print("Apollo console closed. See you on the next mission.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
