"""Original DSKY teaching panel with scripted telemetry, not AGC execution."""

import math


KEYPAD = (
    ("VERB", "+", "7", "8", "9"),
    ("NOUN", "-", "4", "5", "6"),
    ("CLR", "0", "1", "2", "3"),
    ("KEYREL", "ENTR", "RSET", "PRO", ""),
)
LAMPS = ("COMP ACTY", "UPLINK ACTY", "TEMP", "NO ATT", "GIMBAL LOCK",
         "STBY", "PROG", "KEY REL", "RESTART", "OPR ERR", "TRACKER")
HELP = (
    ("V35 E", "Test all lights for five seconds"),
    ("V37 E 63 E", "Start / replay the 90-second descent"),
    ("V16 N60 E", "Monitor horizontal speed, rate, altitude"),
    ("V16 N63 E", "Monitor total speed, rate, altitude"),
    ("V16 N65 E", "Monitor the panel's mission clock"),
    ("V06 N60 E", "Take one snapshot of the descent"),
    ("V05 N09 E", "Read the three alarm-code registers"),
    ("V37 E 00 E", "Select idle; stop the descent"),
    ("V36 E", "Fresh start of this teaching panel"),
)
SEGMENTS = {
    "0": (" _ ", "| |", "|_|"), "1": ("   ", "  |", "  |"),
    "2": (" _ ", " _|", "|_ "), "3": (" _ ", " _|", " _|"),
    "4": ("   ", "|_|", "  |"), "5": (" _ ", "|_ ", " _|"),
    "6": (" _ ", "|_ ", "|_|"), "7": (" _ ", "  |", "  |"),
    "8": (" _ ", "|_|", "|_|"), "9": (" _ ", "|_|", " _|"),
    "+": ("   ", " + ", "   "), "-": ("   ", " - ", "   "),
    ".": (" ", " ", "."), "_": ("   ", "   ", "___"),
}


def digits(value):
    return tuple(" ".join(SEGMENTS[char][row] for char in value) for row in range(3))


def decimal(value, places=0):
    number = f"{round(abs(value) * 10 ** places):05d}"
    if places:
        number = number[:-places] + "." + number[-places:]
    return ("-" if value < 0 else "+") + number


class Dsky:
    def __init__(self):
        self.reset()
        self.restart_left = 0

    def reset(self):
        self.program = self.verb = self.noun = "00"
        self.editing = self.buffer = ""
        self.clock = self.elapsed = self.lamp_left = 0.0
        self.restart_left = 3.0
        self.running = self.alert = self.alarm_seen = self.error = False
        self.monitor = False
        self.source = "60"
        self.snapshot = ("+0000.0", "+0000.0", "+00000")
        self.alarms = [0, 0, 0]
        self.message = "Start: V37 E 63 E | V35 E lights | ? commands"
        self.last_key, self.key_left = "", 0.0

    @property
    def phase(self):
        if self.alert:
            return "OVERLOAD / WAITING FOR PRO"
        if not self.running:
            return "CONTACT / ARZI HAS LANDED" if self.elapsed >= 90 else "P00 / STANDBY"
        return "P63 / BRAKING" if self.elapsed < 45 else "P64 / APPROACH" if self.elapsed < 70 else "P66 / FINAL DESCENT"

    def telemetry(self):
        # shortcut: invented keyframes; replace with an AGC engine for flight simulation.
        points = ((0, 520, -120, 12500), (25, 130, -60, 2400),
                  (45, 55, -20, 600), (65, 18, -8, 120),
                  (80, 2, -2, 16), (90, 0, 0, 0))
        for left, right in zip(points, points[1:]):
            if self.elapsed <= right[0]:
                mix = (self.elapsed - left[0]) / (right[0] - left[0])
                return tuple(a + (b - a) * mix for a, b in zip(left[1:], right[1:]))
        return (0, 0, 0)

    def read(self, noun):
        if noun in ("60", "63"):
            horizontal, vertical, altitude = self.telemetry()
            speed = horizontal if noun == "60" else math.hypot(horizontal, vertical)
            return decimal(speed, 1), decimal(vertical, 1), decimal(altitude)
        if noun == "65":
            hundredths = int(self.clock * 100)
            return decimal(hundredths // 360000), decimal(hundredths // 6000 % 60), decimal(hundredths % 6000 / 100, 2)
        return tuple(f"{code:05o}" for code in self.alarms)

    @property
    def registers(self):
        if self.lamp_left:
            return ("+8888.8", "+8888.8", "+88888")
        return self.read(self.source) if self.monitor else self.snapshot

    @property
    def labels(self):
        if self.lamp_left:
            return ("R1 / SEGMENTS", "R2 / SEGMENTS", "R3 / SEGMENTS")
        if self.source == "65":
            return ("R1 HOURS", "R2 MINUTES", "R3 SECONDS")
        if self.source == "09":
            return ("R1 ALARM / OCT", "R2 ALARM / OCT", "R3 ALARM / OCT")
        return ("R1 HORZ ft/s" if self.source == "60" else "R1 SPEED ft/s", "R2 VERT ft/s", "R3 ALT ft")

    def field(self, name):
        if self.lamp_left:
            return "88"
        return self.buffer.ljust(2, "_") if self.editing == name else getattr(self, name)

    def lit(self, lamp):
        if self.lamp_left:
            return True
        return {
            "COMP ACTY": self.running and not self.alert and int(self.clock * 4) % 2 == 0,
            "STBY": not self.running,
            "PROG": self.alert,
            "KEY REL": bool(self.editing),
            "RESTART": self.restart_left > 0,
            "OPR ERR": self.error,
        }.get(lamp, False)

    def advance(self, seconds):
        if not math.isfinite(seconds) or seconds < 0:
            raise ValueError("Panel time must advance by a finite, nonnegative amount")
        self.clock += seconds
        self.lamp_left = max(0, self.lamp_left - seconds)
        self.restart_left = max(0, self.restart_left - seconds)
        self.key_left = max(0, self.key_left - seconds)
        if not self.running or self.alert:
            return
        self.elapsed = min(90, self.elapsed + seconds)
        if not self.alarm_seen and self.elapsed >= 35:
            self.elapsed = 35
            self.alert = self.alarm_seen = True
            self.alarms = [0o1202] + self.alarms[:2]
            self.message = "01202 scripted overload. Press PRO to continue."
        elif self.elapsed >= 90:
            self.running, self.program = False, "00"
            self.message = "CONTACT. Engine off. Arzi has landed."
        else:
            self.program = "63" if self.elapsed < 45 else "64" if self.elapsed < 70 else "66"

    def reject(self, message):
        self.error, self.message = True, message

    def press(self, key):
        self.last_key, self.key_left = key, 0.18
        if key in ("VERB", "NOUN"):
            if key == "NOUN" and self.editing == "verb":
                if len(self.buffer) != 2:
                    self.reject("VERB needs two digits. C clears; K cancels.")
                    return
                self.verb = self.buffer
            self.editing, self.buffer = key.lower(), ""
        elif len(key) == 1 and key in "0123456789":
            if self.editing and len(self.buffer) < 2:
                self.buffer += key
            else:
                self.reject("Select VERB or NOUN; enter exactly two digits.")
        elif key == "CLR":
            self.buffer = ""
            self.message = "Entry cleared. Type two digits, then ENTR."
        elif key == "BACKSPACE":
            self.buffer = self.buffer[:-1]
        elif key == "KEYREL":
            self.editing = self.buffer = ""
            self.message = "Keyboard released. ? shows the command list."
        elif key == "RSET":
            self.error, self.restart_left = False, 0
            self.message = "OPR ERR reset. P continues the descent alarm." if self.alert else "Indicators reset. ? shows the command list."
        elif key == "PRO":
            if self.alert:
                self.alert = False
                self.restart_left = 3
                self.message = "Alarm acknowledged. Guidance resumes; history retained."
            else:
                self.message = "Ready. V37 E 63 E starts the scripted descent."
        elif key in ("+", "-"):
            self.reject("Registers are read-only; signed loading is unavailable.")
        elif key == "ENTR":
            if self.editing:
                if len(self.buffer) != 2:
                    self.reject("Enter two digits. C clears; K cancels.")
                    return
                field, value = self.editing, self.buffer
                self.editing = self.buffer = ""
                if field == "program":
                    self.select_program(value)
                    return
                setattr(self, field, value)
            self.execute()

    def select_program(self, value):
        if value not in ("00", "63"):
            self.reject("Use P00 idle or P63 scripted descent.")
            return
        self.program = value
        self.running, self.alert = value == "63", False
        if self.running:
            self.elapsed = 0
            self.alarm_seen = False
            self.verb, self.noun, self.source, self.monitor = "16", "60", "60", True
            self.message = "Braking burn. Watch the readings; P continues alarms."
        else:
            self.message = "P00 selected. Descent stopped; telemetry holds."

    def execute(self):
        if self.verb == "35":
            self.lamp_left = 5
            self.message = "Lamp test: all indicators lit for five seconds."
        elif self.verb == "37":
            self.editing, self.buffer = "program", ""
            self.message = "Select 63 descent or 00 idle, then ENTR."
        elif self.verb == "36":
            self.reset()
        elif (self.verb in ("06", "16") and self.noun in ("60", "63", "65")) or (self.verb == "05" and self.noun == "09"):
            self.source = self.noun
            self.monitor = self.verb == "16"
            self.snapshot = self.read(self.source)
            self.message = f"{'Monitoring' if self.monitor else 'Snapshot'} N{self.noun}. Press ? for units and commands."
        else:
            self.reject("Unsupported command. Press ? for supported commands.")
