"""Read-only Z-A v2.0.2 EX1/EX2 Rare/PID GDB evidence recorder.

In GDB after attaching to AArch64 target:
  source scripts/gdb/za_ex_rare_trace.py
  za_trace_start 0xRUNTIME_ELF_VA_BIAS EX1 za_ex1.jsonl
  continue
  ... trigger EX1 Diancie battle, then interrupt ...
  za_trace_stop

For EX2, repeat with label EX2 and separate JSONL.
The first argument is runtime_pc - ELF_static_virtual_address, not an assumed
exefs module base. Instruction fingerprints MUST match before installing bps.
No target memory writes, register changes, or patches are performed here.
"""
from __future__ import annotations

import json
from pathlib import Path
import time
import gdb

# Verified in SHA256 470d6e71e27744a65ac6f1f94587dd34d24e0e2c0da9fd912eb1db03ee848d4d.
ELF_SHA256="470d6e71e27744a65ac6f1f94587dd34d24e0e2c0da9fd912eb1db03ee848d4d"
# 4-byte code fingerprints (AArch64 little endian): abort if any do not match.
PROBES={
    0xE5D20C:bytes.fromhex("29000452"),  # EOR W9,W1,#0x10000000
    0x657168:bytes.fromhex("26182094"),  # BL 0xE5D200
    0x656298:bytes.fromhex("3a030094"),  # BL 0x656F80
    0xE3EB64:bytes.fromhex("0761e097"),  # BL 0x656F80
}
SITES={
    "builder_entry":0x656060,
    "rare_raw_load":0x656144,
    "rare_to_mode":0x65614C,
    "mode_override":0x656160,
    "mode_save":0x656170,
    "builder_before_generator":0x656298,
    "native_generator_entry":0x656F80,
    "native_mode_dispatch":0x657078,
    "native_random_xor_check":0x657124,
    "native_never_antishiny_call":0x657168,
    "native_always_adjust_call":0x657198,
    "native_pid_result":0x6571A4,
    "native_anti_shiny_entry":0xE5D200,
    "native_anti_shiny_return":0xE5D218,
    "native_shiny_xor_entry":0xE5D1E8,
    "desc_always_mode_load":0x653F34,
    "desc_always_mode_compare":0x653F38,
    "field_init_generator":0xE3EB64,
    "field_init_pid_setter_call":0xE3EBA8,
    "pid_setter_entry":0xE57350,
}

class State:
    def __init__(self):
        self.breakpoints=[]
        self.stream=None
        self.label=None
        self.bias=None
        self.total=0
        self.max_hits=15000
STATE=State()

def reg(name):
    try:
        return int(gdb.parse_and_eval("$"+name))&0xFFFFFFFFFFFFFFFF
    except (gdb.error,ValueError):
        return None

def read_uint(addr,width):
    try:
        data=gdb.selected_inferior().read_memory(addr,width).tobytes()
        return int.from_bytes(data,"little")
    except (gdb.error,MemoryError,ValueError):
        return None

def write_event(name,elf_va,extra=None):
    if STATE.stream is None:return
    regs={k:reg(k) for k in ("pc","lr","sp","x0","x1","x2","x3","x8","x9","x19","x20","x21","x22","x24")}
    item={"event":name,"label":STATE.label,"elf_static_va":f"0x{elf_va:X}",
          "runtime_pc":f"0x{STATE.bias+elf_va:X}" if elf_va else None,
          "host_unix_ns":time.time_ns(),"regs":{k:f"0x{v:X}" for k,v in regs.items() if v is not None}}
    if extra:item["values"]={k:(f"0x{v:X}" if isinstance(v,int) else v) for k,v in extra.items()}
    STATE.stream.write(json.dumps(item,ensure_ascii=False)+"\n")
    STATE.stream.flush()

class TracePoint(gdb.Breakpoint):
    def __init__(self,name,va,bias):
        super().__init__(f"*0x{bias+va:X}",type=gdb.BP_BREAKPOINT,internal=False)
        self.name=name
        self.va=va
        self.silent=True

    def stop(self):
        STATE.total+=1
        if STATE.total>STATE.max_hits:
            self.enabled=False
            return False
        name=self.name
        extra={}
        if name in ("rare_raw_load","rare_to_mode","mode_override","mode_save"):
            p=reg("x20")
            if p is not None:
                extra["descriptor_address"]=p
                extra["descriptor_plus68_u32"]=read_uint(p+0x68,4)
                extra["descriptor_plus6c_u32"]=read_uint(p+0x6c,4)
            if name in ("rare_to_mode","mode_override","mode_save"):
                extra["mode_working_x8"]=reg("x8")
        elif name in ("desc_always_mode_load","desc_always_mode_compare"):
            p=reg("x24")
            if p is not None:
                extra["descriptor_address"]=p
                extra["descriptor_plus68_u32"]=read_uint(p+0x68,4)
        elif name=="builder_before_generator":
            p=reg("x0")
            if p is not None:
                extra["state_plus20_mode_u64"]=read_uint(p+0x20,8)
                extra["state_plus28_roll_count_u8"]=read_uint(p+0x28,1)
        elif name in ("native_generator_entry","native_mode_dispatch","native_pid_result"):
            p=reg("x0") if name=="native_generator_entry" else reg("x19")
            if p is not None:
                extra["generator_state_address"]=p
                extra["state_plus20_u64"]=read_uint(p+0x20,8)
                extra["state_plus28_roll_count_u8"]=read_uint(p+0x28,1)
                extra["state_plus18_u32"]=read_uint(p+0x18,4)
        elif name in ("native_anti_shiny_entry","native_shiny_xor_entry"):
            extra["arg_w0_id32_candidate"]=reg("x0") & 0xFFFFFFFF if reg("x0") is not None else None
            extra["arg_w1_pid_candidate"]=reg("x1") & 0xFFFFFFFF if reg("x1") is not None else None
        elif name in ("native_anti_shiny_return","field_init_pid_setter_call","pid_setter_entry"):
            extra["w0_result_or_ptr"]=reg("x0") & 0xFFFFFFFF if reg("x0") is not None else None
            extra["w1_pid_candidate"]=reg("x1") & 0xFFFFFFFF if reg("x1") is not None else None
        write_event(name,self.va,extra)
        return False  # auto-continue; never write to target memory

def stop_trace():
    for b in STATE.breakpoints:
        try:b.delete()
        except gdb.error:pass
    STATE.breakpoints.clear()
    if STATE.stream:
        write_event("trace_stopped",0,{"total_breakpoint_hits":STATE.total})
        STATE.stream.close()
        STATE.stream=None
    STATE.label=None
    STATE.bias=None

class Start(gdb.Command):
    """za_trace_start <runtime_minus_ELF_VA> <EX1|EX2|CONTROL> <output.jsonl>"""
    def __init__(self):super().__init__("za_trace_start",gdb.COMMAND_USER)
    def invoke(self,arg,from_tty):
        argv=gdb.string_to_argv(arg)
        if len(argv)!=3:
            raise gdb.GdbError("Usage: za_trace_start 0xBIAS EX1|EX2|CONTROL out.jsonl")
        bias=int(argv[0],0)
        label=argv[1].upper()
        if label not in ("EX1","EX2","CONTROL"):
            raise gdb.GdbError("Label must be EX1, EX2, or CONTROL")
        if bias<0:raise gdb.GdbError("Negative bias not supported")
        # Mandatory fingerprint validation protects against version/mapping mistakes.
        for va,expected in PROBES.items():
            try:actual=gdb.selected_inferior().read_memory(bias+va,4).tobytes()
            except gdb.error as e:raise gdb.GdbError(f"Unmapped probe at {bias+va:#x}: {e}")
            if actual!=expected:
                raise gdb.GdbError(f"Mismatch VA {va:#x}: runtime bytes {actual.hex()} != {expected.hex()}. "
                                   "Incorrect ELF/Build ID or runtime bias. No breakpoints installed.")
        stop_trace()
        path=Path(argv[2]).expanduser()
        path.parent.mkdir(parents=True,exist_ok=True)
        STATE.stream=path.open("w",encoding="utf-8",buffering=1)
        STATE.label=label
        STATE.bias=bias
        STATE.total=0
        write_event("trace_started",0,{"elf_sha256":ELF_SHA256,"verified_probe_count":len(PROBES),
                                      "note":"Label selected manually: not proof the labeled battle executed"})
        try:
            for name,va in SITES.items():
                STATE.breakpoints.append(TracePoint(name,va,bias))
        except Exception:
            stop_trace()
            raise
        gdb.write(f"ZA read-only trace: {label}, {len(STATE.breakpoints)} breakpoints; "
                  f"output={path}; use 'continue', then 'za_trace_stop'.\n")

class Stop(gdb.Command):
    def __init__(self):super().__init__("za_trace_stop",gdb.COMMAND_USER)
    def invoke(self,arg,from_tty):
        n=STATE.total
        stop_trace()
        gdb.write(f"ZA read-only trace stopped; breakpoint hits={n}.\n")

class Mark(gdb.Command):
    """za_trace_mark <human description> : manual marker only, not game-state proof."""
    def __init__(self):super().__init__("za_trace_mark",gdb.COMMAND_USER)
    def invoke(self,arg,from_tty):
        if STATE.stream is None:raise gdb.GdbError("Start trace first")
        write_event("manual_marker",0,{"description":arg.strip()})

Start();Stop();Mark()
