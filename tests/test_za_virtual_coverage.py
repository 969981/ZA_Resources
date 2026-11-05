#!/usr/bin/env python3
import gzip
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "za_virtual_audit", ROOT / "scripts/Audit-ZA-VirtualConversion.py")
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class NativeIndexAuditTests(unittest.TestCase):
    def test_unknown_and_7z_split_reconcile(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            original = repo / audit.ROOT
            (original / "_index").mkdir(parents=True)
            index = original / "_index/file_index.tsv.gz"
            with gzip.open(index, "wt", encoding="utf-8") as w:
                w.write("hash\tpack_index\tpack_name\tvirtual_path\n")
                w.write("0000000000000123\t0\ta\tik_pokemon/large.bntx\n")
                w.write("0000000000000456\t0\ta\t\n")
            desc = repo / "Unpack/v2.0.2/romfs/arc/data.trpfd/descriptor_summary.json"
            desc.parent.mkdir(parents=True)
            desc.write_text(json.dumps({"descriptorFiles": 2}))
            (original / "_index/full-extract-progress.json").write_text(
                json.dumps({"state": "COMPLETE", "nextPack": 13181, "totalPacks": 13181}))
            out = original / "virtual_converted/_index"
            out.mkdir(parents=True)
            with gzip.open(out / "ik_pokemon.jsonl.gz", "wt") as w:
                for name, status in [("ik_pokemon/large.bntx.7z.001", "STRUCTURE_ONLY"),
                                     ("ik_pokemon/large.bntx.7z.002", "VOLUME_PART")]:
                    w.write(json.dumps({"sourcePath": name, "status": status}) + "\n")
            with gzip.open(out / "_unknown.jsonl.gz", "wt") as w:
                w.write(json.dumps({"sourcePath": "_unknown/0000000000000456.bin",
                                    "status": "CONVERTED"}) + "\n")
            report = audit.audit(repo)
            self.assertEqual(report["missingNativePathsCount"], 0)
            self.assertTrue(report["nativePathCoverageComplete"])
            self.assertFalse(report["semanticConversionComplete"])
            self.assertEqual(report["largeFilesFromOriginalSplitArchives"], 1)
            self.assertEqual(report["notFullyConvertedCount"], 1)


if __name__ == "__main__":
    unittest.main()
