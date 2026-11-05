#!/usr/bin/env python3
"""Extract verifiable ExeFS main.npdm META, ACID and ACI0 without changing the original.

Offsets and lengths are read from the source bytes, not hardcoded. All outputs
are derived artifacts in Unpack/v2.0.2/exefs/main.npdm/.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct

NCA = "4a70b3ff963bfe412681185cea68bf55_NCA"
def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def extract_npdm(data: bytes) -> tuple[dict, dict[str, bytes]]:
    if len(data) < 0x80 or data[:4] != b"META":
        raise ValueError("NPDM META signature or header length invalid")
    # META header contains the two raw section slices. Validate actual magic,
    # non-overlap and bounds rather than assuming every NPDM revision is equal.
    aci_offset, aci_size, acid_offset, acid_size = struct.unpack_from("<4I", data, 0x70)
    sections = {}
    intervals = []
    for name, offset, size in (("ACI0", aci_offset, aci_size),
                               ("ACID", acid_offset, acid_size)):
        if not size or offset < 0x80 or offset > len(data) or size > len(data) - offset:
            raise ValueError(f"Out-of-range {name} offset or size")
        raw = data[offset:offset + size]
        if raw[:4] != name.encode("ascii"):
            raise ValueError(f"Wrong {name} signature")
        intervals.append((offset, offset + size, name))
        sections[name] = raw
    a, b = sorted(intervals)
    if a[1] > b[0]:
        raise ValueError("Overlapping NPDM substructures")
    def desc(name: str, off: int, size: int) -> dict:
        raw = sections[name]
        return {"name": name, "offsetHex": f"0x{off:X}", "offset": off,
                "length": size, "sha256": sha256(raw), "magic": raw[:4].decode("ascii"),
                "output": f"{name}.bin"}
    title = data[0x20:0x30].split(b"\0", 1)[0]
    try:
        title_text = title.decode("ascii", errors="strict")
    except UnicodeError:
        title_text = None
    return {
        "sourceMagic": "META",
        "sourceBytes": len(data),
        "sourceSha256": sha256(data),
        "metaHeaderBytes": 0x80,
        "titleFieldRawHex": data[0x20:0x30].hex(),
        "titleAsciiCandidate": title_text,
        "sections": [desc("ACID", acid_offset, acid_size), desc("ACI0", aci_offset, aci_size)],
        "verification": ["META and section magic", "META section offset/length bounds",
                         "non-overlapping sections", "source SHA-256",
                         "exported bytes slice equality"],
        "status": "CONFIRMED_STRUCTURAL",
        "semanticCaution": "The authorization and capability field meanings are not inferred from offsets alone."
    }, sections

def write_npdm(source: Path, output: Path) -> dict:
    raw = source.read_bytes()
    info, sections = extract_npdm(raw)
    output.mkdir(parents=True, exist_ok=True)
    for name, payload in sections.items():
        path = output / f"{name}.bin"
        if path.exists() and path.read_bytes() != payload:
            raise ValueError(f"Existing different output: {path}")
        path.write_bytes(payload)
        assert sha256(path.read_bytes()) == sha256(payload)
    source_copy = output / "main.npdm"
    if source_copy.exists() and source_copy.read_bytes() != raw:
        raise ValueError("Existing main.npdm copy differs")
    source_copy.write_bytes(raw)
    info["originalCopy"] = "main.npdm"
    info["originalSource"] = source.as_posix()
    metadata = output / "metadata.json"
    metadata.write_text(json.dumps(info, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return info

def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    a = p.parse_args()
    root = a.repo_root.resolve()
    src = root / "v2.0.2" / NCA / "0" / "main.npdm"
    out = root / "Unpack" / "v2.0.2" / "exefs" / "main.npdm"
    if not src.is_file():
        p.error(f"Missing NPDM: {src}")
    info = write_npdm(src, out)
    print(json.dumps({"sourceBytes": info["sourceBytes"], "sections": info["sections"]},
                     ensure_ascii=False, indent=2))
if __name__ == "__main__":
    main()
