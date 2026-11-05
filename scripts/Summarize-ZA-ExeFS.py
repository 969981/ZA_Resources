#!/usr/bin/env python3
"""Verify derived ExeFS outputs and write a checked artifact inventory."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

MODULES = ("main", "rtld", "sdk")

def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def build_manifest(root: Path) -> dict:
    out = root / "Unpack" / "v2.0.2" / "exefs"
    info = {"version": "v2.0.2", "kind": "ExeFS extracted file evidence",
            "modules": {}, "npdm": {}, "complete": False,
            "warning": "Runtime semantics are not established by an ELF conversion."}
    for name in MODULES:
        manifest = out / name / "provenance.json"
        if not manifest.is_file():
            info["modules"][name] = {"status": "NOT_EXTRACTED"}
            continue
        item = json.loads(manifest.read_text(encoding="utf-8"))
        for a in item["artifacts"]:
            file = root / a["path"]
            if not file.is_file() or file.stat().st_size != a["size"] or sha(file) != a["sha256"]:
                raise RuntimeError("Artifact SHA256/length mismatch: " + a["path"])
        info["modules"][name] = {
            "status": "VERIFIED_ARTIFACTS",
            "provenance": manifest.relative_to(root).as_posix(),
            "sourceSha256": item["sourceSha256"],
            "buildIdHex": item["nsoBuildIdHex"],
            "elfSize": item["elfSize"],
            "elfSha256": item["elfSha256"],
            "uncompressedNso": item.get("uncompressedNso"),
            "artifacts": item["artifacts"]}
    npdm = out / "main.npdm" / "metadata.json"
    if npdm.is_file():
        m = json.loads(npdm.read_text(encoding="utf-8"))
        for section in m["sections"]:
            p = npdm.parent / section["output"]
            if not p.is_file() or p.stat().st_size != section["length"] or sha(p) != section["sha256"]:
                raise RuntimeError("NPDM section SHA mismatch: " + section["name"])
        raw = npdm.parent / "main.npdm"
        if not raw.is_file() or sha(raw) != m["sourceSha256"]:
            raise RuntimeError("NPDM source copy mismatch")
        info["npdm"] = {"status": "VERIFIED_STRUCTURAL",
                        "sourceSha256": m["sourceSha256"],
                        "sourceBytes": m["sourceBytes"],
                        "sections": m["sections"],
                        "metadata": npdm.relative_to(root).as_posix()}
    else:
        info["npdm"] = {"status": "NOT_EXTRACTED"}
    info["complete"] = all(info["modules"][m]["status"] == "VERIFIED_ARTIFACTS" for m in MODULES) and info["npdm"]["status"] == "VERIFIED_STRUCTURAL"
    out.mkdir(parents=True, exist_ok=True)
    (out / "exefs-manifest.json").write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return info

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = ap.parse_args()
    result = build_manifest(args.repo_root.resolve())
    print(json.dumps({"complete": result["complete"],
                      "modules": {m: result["modules"][m]["status"] for m in MODULES},
                      "npdm": result["npdm"]["status"]}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
