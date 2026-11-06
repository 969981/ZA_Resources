# Read-only ZA v2.0.2 GDB Python breakpoint recorder.
# USAGE:
#   (gdb) target remote HOST:PORT
#   (gdb) set $za_main = ACTUAL_RUNTIME_MAIN_MODULE_BASE
#   (gdb) source scripts/gdb/za_v202_pid_shiny_trace.py
#   (gdb) za-shiny-breaks core
#   (gdb) continue
# For optional high-traffic helpers: za-shiny-breaks full
# Disable with: za-shiny-clear
#
# REQUIRED: the live main Build ID must match B1F12FD919EAE86A...
# No writes to game memory, PID, files, or saves are performed.
# Sampling does not establish the source of Encounter.rare.

import datetime
import json
import pathlib
import gdb

TRACE_FILE = pathlib.Path("za_v202_pid_shiny_trace.jsonl")
LIMIT_PER_SITE = 300
OFFSETS = {
    "PID_TID_Shiny_Check": 0xE5D1E8,
    "PID_Shiny_Mode_Classify": 0xE5D244,
    "PID_Shiny_Mode_Set": 0xE46024,
    "PID_Shiny_Mode_Adjust": 0xE5D284,
    "PID_Setter": 0xE57350,
    "PID_Ensure_Shiny_Candidate": 0xE45F7C,
}
_breakpoints = []


def register_value(name):
    try:
        return int(gdb.selected_frame().read_register(name)) & 0xFFFFFFFFFFFFFFFF
    except (gdb.error, ValueError, AttributeError):
        return None


class ZABreakpoint(gdb.Breakpoint):
    def __init__(self, base, name, relative):
        super().__init__("*0x%X" % (base + relative),
                         type=gdb.BP_BREAKPOINT,
                         internal=False)
        self.base = base
        self.name = name
        self.relative = relative
        self.seen = 0
        self.silent = True

    def stop(self):
        self.seen += 1
        if self.seen > LIMIT_PER_SITE:
            self.enabled = False
            gdb.write("[ZA] %s reached cap, disabled\n" % self.name)
            return False
        regnames = ("pc", "lr", "sp", "x0", "x1", "x2", "x3", "x8", "x9", "x20")
        registers = {x: register_value(x) for x in regnames}
        try:
            frame = gdb.selected_frame()
            thread = gdb.selected_thread()
            thread_num = thread.num if thread else None
            instructions = gdb.execute("x/6i $pc", to_string=True)
        except (gdb.error, RuntimeError):
            thread_num, instructions = None, "unavailable"
        doc = {
            "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "buildIdExpected": "B1F12FD919EAE86AB8A978317677E64BCE443D1F",
            "site": self.name,
            "siteRva": "0x%X" % self.relative,
            "mainBase": "0x%X" % self.base,
            "thread": thread_num,
            "registers": {k: ("0x%X" % v if v is not None else None)
                          for k, v in registers.items()},
            "assembly": instructions,
            "evidenceLevel": "E4_runtime_breakpoint_unattributed_to_encounter",
        }
        with TRACE_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")
        if self.seen <= 5:
            gdb.write("[ZA] hit %s at main+0x%X; x0=0x%X x1=0x%X\n" %
                      (self.name, self.relative,
                       registers["x0"] or 0, registers["x1"] or 0))
        return False  # Continue guest. No game-side mutation.


class ZAShinyBreaks(gdb.Command):
    """za-shiny-breaks core|full: enable read-only PID/shiny tracepoints."""
    def __init__(self):
        super().__init__("za-shiny-breaks", gdb.COMMAND_USER)
    def invoke(self, argument, from_tty):
        parts = argument.strip().split()
        mode = parts[0] if parts else "core"
        if mode not in ("core", "full"):
            raise gdb.GdbError("Usage: za-shiny-breaks core|full")
        try:
            base = int(gdb.parse_and_eval("$za_main"))
        except (gdb.error, TypeError, ValueError):
            raise gdb.GdbError("First set $za_main to the live main module base")
        if base <= 0:
            raise gdb.GdbError("$za_main must be a nonzero runtime address")
        if _breakpoints:
            raise gdb.GdbError("Already active; use za-shiny-clear first")
        for name, off in OFFSETS.items():
            if mode == "core" and name not in (
                    "PID_Shiny_Mode_Set", "PID_Shiny_Mode_Adjust", "PID_Setter"):
                continue
            _breakpoints.append(ZABreakpoint(base, name, off))
        gdb.write("[ZA] %d read-only breakpoints; JSONL: %s\n" %
                  (len(_breakpoints), TRACE_FILE))


class ZAShinyClear(gdb.Command):
    """za-shiny-clear: disable/delete created ZA tracepoints."""
    def __init__(self):
        super().__init__("za-shiny-clear", gdb.COMMAND_USER)
    def invoke(self, argument, from_tty):
        for b in _breakpoints:
            try:
                b.delete()
            except gdb.error:
                pass
        n = len(_breakpoints)
        _breakpoints.clear()
        gdb.write("[ZA] removed %d tracepoints\n" % n)


ZAShinyBreaks()
ZAShinyClear()
gdb.write("[ZA] loaded. Set $za_main and execute za-shiny-breaks core\n")
