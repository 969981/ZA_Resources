"""Synthetic verification of runtime export log and output bytes."""
import importlib.util
import json
from pathlib import Path
import hashlib
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("trinity_report", ROOT / "scripts" / "Summarize-ZA-Trinity.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class TestTrinityReport(unittest.TestCase):
    def test_rehash_and_dedup(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            out = root / "virtual" / "test"
            out.mkdir(parents=True)
            b = b"native-payload"
            (out / "sample.bin").write_bytes(b)
            row = {
                "Status": "OK", "Hash": "1234567890ABCDEF",
                "Name": "test/sample.bin",
                "Sha256": hashlib.sha256(b).hexdigest().upper(),
                "Size": len(b), "PackName": "sample",
                "PackOffset": 0, "Error": None
            }
            ix = root / "_index"
            ix.mkdir()
            (ix / "export.jsonl").write_text(json.dumps(row) + "\n", encoding="utf8")
            result = module.summarize(root)
            self.assertEqual(result["verifiedExtractedFileCount"], 1)
            self.assertEqual(result["failedFileCount"], 0)
            (out / "sample.bin").write_bytes(b"corrupt")
            with self.assertRaises(RuntimeError):
                module.summarize(root)

if __name__ == "__main__":
    unittest.main()
