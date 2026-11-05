#!/usr/bin/env python3
"""Validate and publish four independently extracted ZA v2.0.2 Lua files.

Input is *only* the GitHub Actions artifact from the successful native four-pack
decode, not a fresh 4.75 GB archive restore. Writes only verified native files
and derived evidence. Never overwrites the previously published 2-pack smoke
results or original ROM contents. No inferred Lua names are introduced.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import shutil
from collections import Counter
from pathlib import Path

ROOT_REL = Path("Unpack/v2.0.2/romfs/arc/data.trpfs")
PINNED_RUN = 42011668436
PINNED_ARTIFACT = 13407204049
PACKS = {
    "dll_util": (12145, "2B9CEDBD307F613F", 16479,
                 "cc77b9440afeef775baf29aeeae381c37458a38e2920e2a162b0679c4d1b8af2"),
    "event_ik": (12146, "7A89AC5CAD9881B3", 7666228,
                 "f238160475095b02e8c5302d907adbd1b48b2fd793a4a8c72ee8c9689fdfd698"),
    "main": (12147, "BE21E65463B9A98F", 478571,
             "d9677f20ab3dfe350eec746d06769cf244bf316ee27fbd73a4bc208e5ff1b8a8"),
    "main_dynamic": (12148, "AFB44A97ABCB6477", 16479,
                     "cc77b9440afeef775baf29aeeae381c37458a38e2920e2a162b0679c4d1b8af2"),
}
TRPFD_SHA = "d1beb3763deab33691c5930e026006278f4586dac094f8d0ea2494ecb6f851f8"
TRPFS_SHA = "64169ef62030dd8e39bb884aff885fd51e7c0758c595c64c4b3fb7b6dad9683d"
NATIVE_TABLES = {
    "native-c-f-method-edges.tsv": 3064,
    "native-c-s-static-edges.tsv": 878,
    "native-unknown-constants.tsv": 1365,
    "native-unknown-opcode-references.tsv": 2140,
}

def digest(p: Path) -> str:
    with p.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()

def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def check_unique_files(root: Path, prefix: str) -> None:
    if not root.is_dir():
        raise ValueError(f"Missing {prefix} root {root}")

def validate(artifact: Path, repo: Path) -> dict:
    artifact = artifact.resolve()
    repo = repo.resolve()
    index = artifact / "_index"
    native = index / "lua-native"
    existing = repo / ROOT_REL / "_index"
    check_unique_files(index, "artifact index")
    check_unique_files(native, "artifact native")
    check_unique_files(existing, "repository index")
    plan = read_json(index / "lua_pack_locations.json")
    anchor = read_json(existing / "lua_pack_locations.json")
    if (plan["version"] != "v2.0.2" or anchor["version"] != "v2.0.2" or
        plan["target_pack_indices"] != [12145,12146,12147,12148] or
        anchor["target_pack_indices"] != plan["target_pack_indices"] or
        plan["all_unique"] is not True or anchor["all_unique"] is not True or
        plan["descriptor_files_scanned"] != 238546):
        raise ValueError("Missing or inconsistent verified TRPFD native pack list")
    restore = read_json(index / "trpfs-restore.json")
    originals = {x["path"]: x for x in restore.get("originals", [])}
    if (restore.get("status") != "CONFIRMED_ORIGINAL_BYTES" or
        originals["arc/data.trpfd"]["sha256"].lower() != TRPFD_SHA or
        originals["arc/data.trpfs"]["sha256"].lower() != TRPFS_SHA or
        originals["arc/data.trpfs"]["archiveVolumes"] != 87):
        raise ValueError("Original 87-volume Trinity restore is not verified")
    batch = read_json(index / "batch_summary.json")
    total_size = sum(x[2] for x in PACKS.values())
    if (batch["status"] != "VERIFIED_WINDOW" or
        batch["verifiedExtractedFileCount"] != 4 or
        batch["verifiedExtractedBytes"] != total_size or
        batch["failedFileCount"] != 0 or
        batch["uniqueHashEntries"] != 4):
        raise ValueError("Failed/unverified native Lua extraction batch")
    export = [json.loads(s) for s in (index / "export.jsonl").read_text(
        encoding="utf-8-sig").splitlines() if s.strip()]
    if len(export) != 4 or len({x["Hash"] for x in export}) != 4:
        raise ValueError("Expected four unique original native file records")
    export_by_hash = {x["Hash"].upper(): x for x in export}
    summary = read_json(native / "native-lua-summary.json")
    if (summary["version"] != "v2.0.2" or
        summary["native_files_parsed"] != 4 or
        summary["native_files_missing"] != 0 or
        summary["native_files_unsupported"] != 0 or
        summary["native_original_name_confirmations"] != 0):
        raise ValueError("Native Lua 5.4 parse was incomplete or overstated")
    computed = {}
    for name, (pack, file_hash, expected_size, expected_sha) in PACKS.items():
        rel = f"script/lua/bin/release/{name}/{name}.blua"
        match = plan["targets"][name]["matches"]
        original_match = anchor["targets"][name]["matches"]
        if (len(match) != 1 or len(original_match) != 1 or
            match[0]["pack_index"] != pack or original_match[0]["pack_index"] != pack or
            match[0]["hash"].upper() != file_hash or original_match[0]["hash"].upper() != file_hash or
            match[0]["virtual_path"] != rel or original_match[0]["virtual_path"] != rel):
            raise ValueError("Native descriptor identity mismatch for "+name)
        entry = export_by_hash.get(file_hash)
        if (not entry or entry["Status"] != "OK" or entry["Name"] != rel or
            entry["Size"] != expected_size or entry["Sha256"].lower() != expected_sha or
            entry["Error"] is not None):
            raise ValueError("Native export log mismatch for "+name)
        file = artifact / "virtual" / rel
        if not file.is_file() or file.stat().st_size != expected_size:
            raise ValueError("Native virtual file missing or size changed: "+name)
        sha = digest(file)
        if sha != expected_sha or file.read_bytes()[:12] != b"\x1bLua\x54\x00\x19\x93\r\n\x1a\n":
            raise ValueError("Native bytecode is not the verified original: "+name)
        parsed = summary["files"][name]
        if (parsed["status"] != "PARSED_NATIVE_LUA54" or
            parsed["bytes"] != expected_size or
            parsed["sha256"].lower() != sha or
            parsed["source_pack_index"] != pack):
            raise ValueError("Lua parser provenance disagrees: "+name)
        computed[name] = {"sha256": sha, "size": expected_size, "pack": pack,
                          "virtual_path": rel, "prototypes": parsed["prototypes"]}
    if sum(x["prototypes"] for x in computed.values()) != 9222:
        raise ValueError("Lua native prototype totals changed")
    for filename, expected_rows in NATIVE_TABLES.items():
        file = native / filename
        with file.open(encoding="utf-8-sig", newline="") as fh:
            lines = list(csv.DictReader(fh, delimiter="\t"))
        if len(lines) != expected_rows:
            raise ValueError("Native analysis rows missing: " + filename)
    if (summary["native_unknown_opcode_references"] != 2140 or
        summary["native_unknown_constant_occurrences"] != 1365 or
        summary["native_class_f_closure_edges"] != 3064 or
        summary["native_class_s_closure_edges"] != 878):
        raise ValueError("Native opcode/constant evidence totals mismatch")
    return {
        "status": "VERIFIED_NATIVE_LUA_FOUR_PACK_PUBLISH",
        "version": "v2.0.2",
        "source_workflow_run": PINNED_RUN,
        "source_artifact_id": PINNED_ARTIFACT,
        "original_trpfd_sha256": TRPFD_SHA,
        "original_trpfs_sha256": TRPFS_SHA,
        "targets": computed,
        "native_opcode_reference_rows": 2140,
        "native_names_confirmed": 0,
        "note": "TRPFS source and extracted game Lua were verified. Hash opcode evidence does not recover original names."
    }

def copy_checked(source: Path, dest: Path) -> str:
    if dest.is_file():
        if digest(source) != digest(dest):
            raise ValueError("Existing published file differs, refusing overwrite: " + str(dest))
        return "unchanged"
    if dest.exists():
        raise ValueError("Destination conflicts with a nonfile: " + str(dest))
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)
    if digest(source) != digest(dest):
        raise ValueError("Copied file failed SHA256 verification: " + str(dest))
    return "copied"

def publish(artifact: Path, repo: Path) -> dict:
    report = validate(artifact, repo)
    destination = repo.resolve() / ROOT_REL
    source = artifact.resolve()
    copied = []
    for name in PACKS:
        rel = f"script/lua/bin/release/{name}/{name}.blua"
        path = "virtual/" + rel
        status = copy_checked(source / path, destination / path)
        copied.append({"path": path, "status": status})
    for filename in [*NATIVE_TABLES, "native-lua-summary.json"]:
        path = "_index/lua-native/" + filename
        status = copy_checked(source / path, destination / path)
        copied.append({"path": path, "status": status})
    for initial, published in [
        ("export.jsonl", "lua-target-export.jsonl"),
        ("batch_summary.json", "lua-target-batch-summary.json"),
        ("trpfs-restore.json", "lua-target-trpfs-restore.json"),
    ]:
        path = "_index/lua-native/" + published
        status = copy_checked(source / "_index" / initial, destination / path)
        copied.append({"path": path, "status": status})
    proof = destination / "_index/lua-native/lua-target-publish-proof.json"
    proof_bytes = (json.dumps(report, ensure_ascii=False, indent=2)+"\n").encode("utf-8")
    if proof.exists() and proof.read_bytes() != proof_bytes:
        raise ValueError("Published proof conflicts; please investigate before replacing")
    proof.parent.mkdir(parents=True, exist_ok=True)
    proof.write_bytes(proof_bytes)
    report["copied"] = copied
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--artifact", type=Path, required=True)
    p.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument("--verify-only", action="store_true")
    args = p.parse_args()
    print(json.dumps(validate(args.artifact,args.repo),ensure_ascii=False,indent=2)
          if args.verify_only else "",flush=True)
    if not args.verify_only:
        publish(args.artifact, args.repo)

if __name__ == "__main__":
    main()
