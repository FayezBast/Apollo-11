"""The launcher's catalog and small, explicitly illustrative demonstrations."""

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = (
    ("sources", "Source explorer", "Read the original Command Module and Lunar Module programs."),
    ("manual", "Command reference", "Keep Apollo's verb and noun sequences close at hand."),
    ("scene", "Arzi descent", "Watch an original terminal animation of the lunar landing."),
    ("alarms", "Alarm laboratory", "Explore memory pressure, overload, and 1201 / 1202 recovery."),
)
MODULES = (("Luminary099", "Arzi / Lunar Module"), ("Comanche055", "Columbia / Command Module"))
COMMANDS = (
    ("V35 E", "Test the lights", "VERB 3 5 ENTR", "Tests the DSKY lights and display segments for about five seconds.", "ASSEMBLY_AND_OPERATION_INFORMATION.agc", 200),
    ("V37 E 00 E", "Select idle program P00", "VERB 3 7 ENTR 0 0 ENTR", "Verb 37 requests a program change. Enter 00 at the program prompt.", "ASSEMBLY_AND_OPERATION_INFORMATION.agc", 202),
    ("V16 N65 E", "Monitor sampled AGC time", "VERB 1 6 NOUN 6 5 ENTR", "Verb 16 monitors decimal data. Noun 65 is sampled AGC time: hours, minutes, seconds.", "ASSEMBLY_AND_OPERATION_INFORMATION.agc", 415),
    ("V05 N09 E", "Read alarm codes", "VERB 0 5 NOUN 0 9 ENTR", "Verb 05 displays octal data. Noun 09 selects the three alarm-code registers.", "ASSEMBLY_AND_OPERATION_INFORMATION.agc", 295),
    ("V91 E", "Inspect fixed-memory checksums", "VERB 9 1 ENTR", "Shows one rope-memory bank at a time. V33 E proceeds to the next bank; V34 E terminates.", "AGC_BLOCK_TWO_SELF_CHECK.agc", 63),
    ("V36 E", "Request a fresh start", "VERB 3 6 ENTR", "Requests the flight software's fresh-start routine. This can interrupt a running program.", "ASSEMBLY_AND_OPERATION_INFORMATION.agc", 201),
)


def source_files(module, root=ROOT):
    if module not in {name for name, _ in MODULES}:
        raise ValueError("Unknown Apollo module")
    return sorted(path.name for path in (root / module).glob("*.agc") if path.is_file())


def read_source(module, name, root=ROOT):
    if name not in source_files(module, root):
        raise ValueError("Choose an assembly file from the source explorer")
    path = (root / module / name).resolve()
    if not path.is_relative_to((root / module).resolve()):
        raise ValueError("Source file leaves the Apollo module")
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


@dataclass
class AlarmDemo:
    """A teaching model of finite pools, not an execution of Luminary."""

    radar: bool = False
    monitor: bool = False
    vac_mode: bool = False
    cores: int = 1
    vacs: int = 0
    elapsed: float = 0
    cycle: float = 0
    restarts: int = 0
    last_alarm: str = "-----"
    message: str = "Healthy cycle. Toggle both RADAR and MONITOR to create overload."

    @property
    def demand(self):
        # shortcut: illustrative load costs; replace with an AGC engine for flight simulation.
        return 0.82 + 0.15 * self.radar + 0.08 * self.monitor

    def select_pool(self, vac_mode):
        self.vac_mode = vac_mode
        self.cores, self.vacs, self.cycle = 1, int(vac_mode), 0
        self.message = "Pool reset. VAC mode demonstrates 1201; core-only mode demonstrates 1202."

    def advance(self, seconds):
        if not 0 <= seconds <= 60:
            raise ValueError("Advance between zero and sixty seconds")
        self.elapsed += seconds
        self.cycle += seconds
        while self.cycle >= 2:
            self.cycle -= 2
            if self.demand <= 1:
                self.cores, self.vacs = 1, int(self.vac_mode)
                self.message = "Guidance finished; its temporary memory was released."
                continue
            if self.vac_mode and self.vacs == 5:
                self.restart("01201")
            elif self.cores == 8:
                self.restart("01202")
            else:
                self.cores += 1
                self.vacs += int(self.vac_mode)
                self.message = "Unfinished guidance work retained memory. Another cycle claimed a slot."

    def restart(self, code):
        self.last_alarm = code
        self.restarts += 1
        self.cores, self.vacs = 1, int(self.vac_mode)
        self.monitor = False
        self.message = f"{code}: restart cleared the backlog and dropped the optional monitor."
