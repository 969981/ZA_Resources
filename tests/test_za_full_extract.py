"""No-ROM regression tests for ZA M2 batch publisher and path/hash helpers."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("za_full", ROOT / "scripts" / "Run-ZA-FullExtract.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def git(cwd, *args):
    return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()

class ZAFullPipelineTests(unittest.TestCase):
    def test_safe_output_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertTrue(str(mod.safe_output(root, "abc/def.bin")).endswith(str(Path("abc/def.bin"))))
            for name in ("../outside", "abc//def", "/abs/path", "C:/data", "abc\\def"):
                with self.assertRaises(ValueError):
                    mod.safe_output(root, name)

    def test_git_bulk_blob_id_lookup_unicode_whitespace_and_missing(self):
        with tempfile.TemporaryDirectory() as d:
            repo=Path(d)
            git(repo,"init")
            git(repo,"config","user.name","ZA Tests")
            git(repo,"config","user.email","tests@example.com")
            virtual=repo/mod.ROOT_REL/"virtual"
            virtual.mkdir(parents=True)
            (virtual/"中文 名称.txt").write_text("alpha",encoding="utf-8")
            (virtual/"second.bin").write_bytes(b"beta")
            git(repo,"add",".")
            git(repo,"commit","-m","native fixtures")
            commit=git(repo,"rev-parse","HEAD")
            paths=[(mod.ROOT_REL/"virtual/中文 名称.txt").as_posix(),
                   (mod.ROOT_REL/"virtual/second.bin").as_posix(),
                   (mod.ROOT_REL/"virtual/missing.bin").as_posix()]
            values=mod._blob_ids(repo,commit,paths)
            self.assertEqual(values[paths[0]],git(repo,"hash-object",paths[0]))
            self.assertEqual(values[paths[1]],git(repo,"hash-object",paths[1]))
            self.assertEqual(values[paths[2]],"")
            self.assertEqual(list(values),paths)

    def test_publisher_does_not_rebase_dirty_worktree(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            bare = tmp / "remote.git"
            repo = tmp / "checkout"
            git(tmp, "init", "--bare", str(bare))
            git(tmp, "clone", str(bare), str(repo))
            git(repo, "config", "user.name", "ZA Unit Tests")
            git(repo, "config", "user.email", "tests@example.com")
            git(repo, "checkout", "-b", "master")
            (repo / "tracked.txt").write_text("before\n")
            git(repo, "add", "tracked.txt")
            git(repo, "commit", "-m", "initial")
            git(repo, "push", "-u", "origin", "master")
            # The preceding ZA smoke job could not pull/rebase when tracked data
            # had local changes; this publisher must not touch those changes.
            (repo / "tracked.txt").write_text("locally modified\n")
            output = mod.ROOT_REL / "_index" / "batches" / "smoke.jsonl"
            target = repo / output
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps({"test": "verified"}) + "\n")
            old_head = git(repo, "rev-parse", "HEAD")
            mod.git_commit_and_push(repo, [output.as_posix()], "verified generated output", False)
            self.assertEqual(git(repo, "rev-parse", "HEAD"), old_head)
            self.assertEqual((repo / "tracked.txt").read_text(), "locally modified\n")
            git(repo, "fetch", "origin", "master")
            self.assertNotEqual(git(repo, "rev-parse", "origin/master"), old_head)
            self.assertEqual(git(repo, "show", "origin/master:tracked.txt"), "before")
            self.assertIn("verified", git(repo, "show", "origin/master:"+output.as_posix()))
            # Same deterministic output cannot accidentally change master.
            mod.git_commit_and_push(repo, [output.as_posix()], "repeat same", False)

if __name__ == "__main__":
    unittest.main()
