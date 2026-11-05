"""Synthetic validation of ZA extracted PCK media and Git-safe archive parts."""
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "Publish-ZA-PCKMedia.py"
spec = importlib.util.spec_from_file_location("za_pck_archive", MODULE)
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


def index(paths=None):
    if paths is None:
        paths = [
            {"path": "ZA_PCK_MEDIA/Stream/stream/sfx/123.wem", "size": 4,
             "sha256": hashlib.sha256(b"RIFF").hexdigest(), "status": "EXTRACTED"},
            {"path": "ZA_PCK_MEDIA/Stream/stream/sfx/124.wem", "size": 3,
             "sha256": hashlib.sha256(b"ABC").hexdigest(), "status": "EXTRACTED"},
        ]
    return {"source": "Stream.pck", "status": "COMPLETE", "items": paths}


class TestArchive(unittest.TestCase):
    def test_index_to_file_tree_sha256_and_missing(self):
        with tempfile.TemporaryDirectory() as t:
            src = Path(t) / "Stream/stream/sfx"
            src.mkdir(parents=True)
            (src / "123.wem").write_bytes(b"RIFF")
            (src / "124.wem").write_bytes(b"ABC")
            expected = a.expected_media(index(), "Stream")
            self.assertEqual(a.check_tree(Path(t) / "Stream", expected), (2, 7))
            (src / "123.wem").write_bytes(b"FAIL")
            with self.assertRaisesRegex(ValueError, "mismatch"):
                a.check_tree(Path(t) / "Stream", expected)
            (src / "123.wem").unlink()
            with self.assertRaisesRegex(ValueError, "Missing"):
                a.check_tree(Path(t) / "Stream", expected)
            (src / "extra.wem").write_bytes(b"X")
            with self.assertRaisesRegex(ValueError, "Undocumented"):
                a.check_tree(Path(t) / "Stream", expected)

    def test_reject_path_escape_and_conflicting_reuse(self):
        for path in ("../bad.wem", "ZA_PCK_MEDIA/Stream/../bad.wem",
                     "ZA_PCK_MEDIA/Other/stream/sfx/1.wem",
                     "ZA_PCK_MEDIA\\Stream\\bad.wem"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                a.expected_media(index([{"path": path, "size": 1,
                      "sha256": "a" * 64, "status": "EXTRACTED"}]), "Stream")
        x = index()["items"][0]
        conflict = {**x, "sha256": "b" * 64}
        with self.assertRaisesRegex(ValueError, "collision"):
            a.expected_media(index([x, conflict]), "Stream")

    def test_contiguous_parts_and_hard_git_limit(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            archive = root / "Stream.pck.media.7z"
            (root / (archive.name + ".001")).write_bytes(b"A")
            (root / (archive.name + ".002")).write_bytes(b"BB")
            self.assertEqual(len(a.inspect_parts(archive)), 2)
            (root / (archive.name + ".001")).unlink()
            with self.assertRaisesRegex(ValueError, "gap"):
                a.inspect_parts(archive)

    def test_cannot_label_incomplete_index_complete(self):
        partial = index()
        partial["status"] = "PARTIAL"
        with self.assertRaises(ValueError):
            a.expected_media(partial, "Stream")
        self.assertEqual(a.MAX_VOLUME, 90 * 1024 * 1024)
        self.assertLess(a.MAX_VOLUME, a.MAX_GIT_BLOB)


if __name__ == "__main__":
    unittest.main()
