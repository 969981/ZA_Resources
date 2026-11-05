#!/usr/bin/env python3
"""Bounds-checked ZA v2.0.2 Wwise BNK/AKPK and opaque TROWC extraction."""
import argparse
import csv
import hashlib
import json
import re
import shutil
import struct
from collections import Counter
from pathlib import Path

AUDIO = Path("audio/wwise/bin/Switch")
CONFIG = Path("system/config/data/trinity_config.trowc")
BUF = 1 << 20

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(BUF), b""):
            h.update(chunk)
    return h.hexdigest()

def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def slice_to(src, offset, length, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha256()
    with src.open("rb") as fin, dst.open("wb") as fout:
        fin.seek(offset)
        remaining = length
        while remaining:
            b = fin.read(min(BUF, remaining))
            if not b:
                raise ValueError(f"truncated slice {src}:{offset}+{length}")
            fout.write(b)
            h.update(b)
            remaining -= len(b)
    return h.hexdigest()

def bnk(src, meta, media):
    size = src.stat().st_size
    sections, media_index = [], []
    data_at = data_size = None
    bank_header = None
    didx = []
    with src.open("rb") as f:
        at = 0
        while at < size:
            if size - at < 8:
                raise ValueError(f"truncated BNK section at {at}")
            f.seek(at)
            tag, n = struct.unpack("<4sI", f.read(8))
            start, end = at + 8, at + 8 + n
            if end > size or not re.fullmatch(rb"[A-Z0-9_]{4}", tag):
                raise ValueError(f"invalid BNK section at {at}")
            name = tag.decode("ascii")
            sec = {"name": name, "offset": at, "length": n}
            if name == "BKHD":
                if n < 8:
                    raise ValueError("short BKHD")
                f.seek(start)
                version, bid = struct.unpack("<II", f.read(8))
                bank_header = {"version": version, "id": bid}
            elif name == "DIDX":
                if n % 12:
                    raise ValueError("nonintegral DIDX")
                f.seek(start)
                didx = [struct.unpack("<III", f.read(12)) for _ in range(n // 12)]
            elif name == "DATA":
                data_at, data_size = start, n
            elif name == "HIRC":
                if n < 4:
                    raise ValueError("short HIRC")
                f.seek(start)
                total = struct.unpack("<I", f.read(4))[0]
                hirc = []
                for _ in range(total):
                    if f.tell() + 5 > end:
                        raise ValueError("truncated HIRC object")
                    kind, length = struct.unpack("<BI", f.read(5))
                    if length < 4 or f.tell() + length > end:
                        raise ValueError("invalid HIRC object size")
                    oid = struct.unpack("<I", f.read(4))[0]
                    hirc.append({"type": kind, "id": oid, "size": length})
                    f.seek(length - 4, 1)
                sec["objects"] = hirc
            sections.append(sec)
            at = end
        if not sections or sections[0]["name"] != "BKHD":
            raise ValueError("not a BNK: BKHD first section missing")
        if didx and data_at is None:
            raise ValueError("DIDX without DATA")
        for fid, offset, n in didx:
            if offset + n > data_size:
                raise ValueError(f"BNK media {fid} escapes DATA")
            absolute = data_at + offset
            f.seek(absolute)
            signature = f.read(4)
            ok = signature in (b"RIFF", b"RIFX")
            target = media / src.stem / f"{fid}{'.wem' if ok else '.bin'}"
            h = slice_to(src, absolute, n, target)
            media_index.append({"id": fid, "offset": absolute, "size": n, "sha256": h,
                                "magic": signature.hex(), "path": target.relative_to(media.parent).as_posix(),
                                "status": "EXTRACTED" if ok else "UNKNOWN_MAGIC"})
    result = {"format": "Wwise BNK", "source": src.name, "sourceSize": size,
              "sourceSha256": sha256(src), "bankHeader": bank_header,
              "sections": sections, "embeddedMedia": media_index,
              "status": "COMPLETE" if all(x["status"] == "EXTRACTED" for x in media_index) else "PARTIAL"}
    write_json(meta / (src.name + ".json"), result)
    return result

def pck(src, meta, media):
    size = src.stat().st_size
    with src.open("rb") as f:
        head = f.read(24)
        if len(head) != 24 or head[:4] != b"AKPK":
            raise ValueError("not an AKPK package")
        order = "<" if struct.unpack_from("<I", head, 8)[0] == 1 else ">"
        header_size, flag, ls, bs, ss = struct.unpack_from(order + "IIIII", head, 4)
        if flag != 1:
            raise ValueError("unsupported AKPK flags/endian")
        es = 0
        if ls + bs + ss + 16 < header_size:
            raw = f.read(4)
            if len(raw) != 4:
                raise ValueError("truncated AKPK fourth table header")
            es = struct.unpack(order + "I", raw)[0]
        fixed = 20 if f.tell() == 28 else 16
        if header_size != fixed + ls + bs + ss + es or header_size + 8 > size:
            raise ValueError("AKPK header sizes do not add up")
        def table(n):
            if n > size or f.tell() + n > size:
                raise ValueError("AKPK table out of bounds")
            return f.read(n)
        lang, banks, sounds = table(ls), table(bs), table(ss)
        external = table(es) if es else b""
        if f.tell() != 8 + header_size or len(lang) < 4:
            raise ValueError("AKPK table terminator invalid")
        u32 = lambda b, off: struct.unpack_from(order + "I", b, off)[0]
        nlang = u32(lang, 0)
        if 4 + nlang * 8 > len(lang):
            raise ValueError("AKPK language records truncated")
        names = {}
        for i in range(nlang):
            off, lid = struct.unpack_from(order + "II", lang, 4 + 8*i)
            if off >= len(lang):
                raise ValueError("AKPK invalid language offset")
            tail = lang[off:]
            if len(tail) > 1 and (tail[0] == 0 or tail[1] == 0):
                terminator = next((j for j in range(0, len(tail)-1, 2) if tail[j:j+2] == b"\x00\x00"), len(tail))
                raw_name = tail[:terminator].decode("utf-16-le" if order == "<" else "utf-16-be", errors="replace")
            else:
                raw_name = tail.split(b"\x00", 1)[0].decode("utf-8", errors="replace")
            names[str(lid)] = re.sub(r"[^a-zA-Z0-9_-]", "_", raw_name) or f"lang_{lid}"
        def entries(blob, kind):
            if not blob:
                return []
            if len(blob) < 4:
                raise ValueError("AKPK missing table count")
            count = u32(blob, 0)
            if not count:
                if len(blob) != 4:
                    raise ValueError("AKPK empty table with extra bytes")
                return []
            if (len(blob) - 4) % count:
                raise ValueError("AKPK irregular table stride")
            stride = (len(blob) - 4) // count
            if stride not in (20, 24):
                raise ValueError(f"AKPK unsupported stride {stride}")
            parsed = []
            for i in range(count):
                at = 4 + stride * i
                if kind == "external" and stride == 24:
                    fid = struct.unpack_from(order + "Q", blob, at)[0]
                    block, n, position, lid = struct.unpack_from(order + "IIII", blob, at+8)
                elif stride == 24:
                    fid, block = struct.unpack_from(order + "II", blob, at)
                    n = struct.unpack_from(order + "Q", blob, at+8)[0]
                    position, lid = struct.unpack_from(order + "II", blob, at+16)
                else:
                    fid, block, n, position, lid = struct.unpack_from(order + "IIIII", blob, at)
                offset = block * position if block else position
                if offset + n > size or (n and offset < 8 + header_size):
                    raise ValueError(f"AKPK entry {fid} out of bounds")
                parsed.append((fid, offset, n, lid))
            return parsed
        extracted = []
        for kind, blob in (("bank", banks), ("stream", sounds), ("external", external)):
            for fid, offset, n, lid in entries(blob, kind):
                f.seek(offset)
                signature = f.read(4)
                ok = signature == (b"BKHD" if kind == "bank" else b"RIFF") or (kind != "bank" and signature == b"RIFX")
                dest = media / src.stem / kind / names.get(str(lid), f"lang_{lid}") / (str(fid) + (".bnk" if kind == "bank" else ".wem") if ok else str(fid) + ".bin")
                h = slice_to(src, offset, n, dest)
                extracted.append({"kind": kind, "id": fid, "languageId": lid,
                                  "offset": offset, "size": n, "magic": signature.hex(), "sha256": h,
                                  "path": dest.relative_to(media.parent).as_posix(),
                                  "status": "EXTRACTED" if ok else "UNKNOWN_MAGIC"})
    result = {"format": "Wwise AKPK", "source": src.name, "sourceSize": size,
              "sourceSha256": sha256(src), "headerSize": header_size,
              "tables": {"languages": ls, "banks": bs, "streams": ss, "externals": es},
              "languages": names, "items": extracted,
              "status": "COMPLETE" if all(x["status"] == "EXTRACTED" for x in extracted) else "PARTIAL"}
    write_json(meta / (src.name + ".json"), result)
    return result

def config(src, dest):
    raw = src.read_bytes()
    strings = [{"offset": m.start(), "value": m.group(1).decode("ascii")}
               for m in re.finditer(rb"([\x20-\x7e]{3,})\x00", raw)]
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dest / src.name)
    with (dest / (src.name + ".strings.tsv")).open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["byteOffset", "string"])
        w.writerows((s["offset"], s["value"]) for s in strings)
    result = {"format": "opaque Trinity TROWC", "sourceSize": len(raw),
              "sourceSha256": hashlib.sha256(raw).hexdigest(),
              "observedNullTerminatedStrings": strings, "status": "PARTIAL",
              "note": "String offsets and lossless bytes confirmed; structured config values UNKNOWN."}
    write_json(dest / (src.name + ".json"), result)
    return result

def process(srcroot, outroot, pck_media, expected):
    srcs = sorted((srcroot / AUDIO).glob("*.bnk")) + sorted((srcroot / AUDIO).glob("*.pck"))
    cfg = srcroot / CONFIG
    if Counter(p.suffix for p in srcs) != {".bnk": 16, ".pck": 3} or not cfg.is_file():
        raise ValueError("Expected exactly 16 BNK + 3 PCK + one TROWC")
    report = []
    for p in [*srcs, cfg]:
        rel = p.relative_to(srcroot).as_posix()
        h = sha256(p)
        if expected and (rel not in expected or expected[rel]["sourceSha256"].lower() != h
                         or int(expected[rel]["sourceSizeBytes"]) != p.stat().st_size):
            raise ValueError(f"source inventory mismatch: {rel}")
        if p.suffix == ".bnk":
            r = bnk(p, outroot / AUDIO / "_index", outroot / AUDIO / "_embedded")
        elif p.suffix == ".pck":
            r = pck(p, outroot / AUDIO / "_index", pck_media)
        else:
            r = config(p, outroot / CONFIG.parent)
        report.append({"sourcePath": rel, "sourceSha256": h,
                       "status": r["status"], "entryCount": len(r.get("embeddedMedia", r.get("items", [])))})
    summary = {"schemaVersion": 1, "version": "v2.0.2", "files": report,
               "processedSourceFiles": len(report),
               "partialFiles": sum(x["status"] != "COMPLETE" for x in report),
               "note": "PARTIAL means an unknown embedded signature or an opaque schema, not missing original bytes."}
    write_json(outroot / "_index" / "remaining-romfs-audit.json", summary)
    return summary

def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--source-root", required=True, type=Path)
    cli.add_argument("--output-root", required=True, type=Path)
    cli.add_argument("--pck-media-root", required=True, type=Path)
    cli.add_argument("--manifest", required=True, type=Path)
    args = cli.parse_args()
    doc = json.loads(args.manifest.read_text(encoding="utf-8-sig"))
    sources = {x["sourceRelativePath"]: x for x in doc["files"]
               if x["sourceRelativePath"].startswith(("audio/", "system/config/"))}
    if len(sources) != 20:
        raise ValueError(f"Expected 20 RomFS audio/config source entries, got {len(sources)}")
    result = process(args.source_root, args.output_root, args.pck_media_root, sources)
    print(json.dumps({"processed": result["processedSourceFiles"], "partial": result["partialFiles"]}))

if __name__ == "__main__":
    main()
