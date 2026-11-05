"""Tests for deterministic manifest and volume verification gates (no proprietary data)."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("restore_trinity", ROOT / "scripts" / "Restore-ZA-TrinityDirect.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class TestTrinityRestore(unittest.TestCase):
    def test_verified_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data.trpfd"
            path.write_bytes(b"native-original")
            import hashlib
            digest = hashlib.sha256(b"native-original").hexdigest()
            self.assertEqual(module.verify(path, 15, digest, "synthetic"), digest)
            with self.assertRaises(ValueError):
                module.verify(path, 15, "0" * 64, "synthetic")
            with self.assertRaises(ValueError):
                module.verify(path, 2, digest, "synthetic")

if __name__ == "__main__":
    unittest.main()
