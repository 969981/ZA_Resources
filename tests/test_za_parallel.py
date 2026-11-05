"""ROM-free tests: real concurrent child processes, isolated paths and SHA-256 merges."""
from __future__ import annotations
import hashlib
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("za_parallel", ROOT / "scripts" / "za_trinity_parallel.py")
parallel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parallel)

FAKE_DECODER = r'''
import argparse, hashlib, json, os
from pathlib import Path
p = argparse.ArgumentParser()
for x in ("romfs","output","cache","oodle","start-pack","max-packs","report"):
    p.add_argument("--"+x, required=True)
a = p.parse_args()
output = Path(a.output)
log = Path(a.report)
log.parent.mkdir(parents=True,exist_ok=True)
with log.open("w",encoding="utf-8") as f:
    for i in range(int(a.start_pack),int(a.start_pack)+int(a.max_packs)):
        name = "same.bin" if os.environ.get("ZA_TEST_COLLISION") else f"assets/{i}.bin"
        body = ("payload-for-"+str(i)).encode("ascii")
        target = output / "virtual" / name
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(body)
        row = {"Status":"OK","Hash":f"{i:016X}","Name":name,
               "OutputPath":str(target),"Sha256":hashlib.sha256(body).hexdigest().upper(),
               "Size":len(body),"PackName":f"testpack_{i}","PackOffset":i,
               "Error":None}
        f.write(json.dumps(row)+"\n")
'''


class ZAParallelNativeTests(unittest.TestCase):
    def test_partition_is_contiguous_bounded_and_disjoint(self):
        self.assertEqual(parallel.ranges(11, 20, 4),
                         [(11,13),(13,15),(15,17),(17,20)])
        self.assertEqual(parallel.ranges(5, 7, 6),[(5,6),(6,7)])
        for v in (0,-1,9):
            with self.assertRaises(ValueError):
                parallel.ranges(2,7,v)

    def test_pack_index_count_and_order(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp)/"pack_index.tsv"
            with p.open("w",encoding="utf-8") as f:
                f.write("pack_index\tpack_name\treferenced_files\tpacked_bytes\treported_file_count\n")
                for i in range(13181):
                    f.write(f"{i}\tpack{i}\t1\t24\t1\n")
            x = parallel.load_pack_counts(p)
            self.assertEqual(len(x),13181)
            self.assertEqual(x[100],1)

    def _params(self, root, start=3, end=11, workers=4):
        decoder = root / "fake_decoder.py"
        decoder.write_text(FAKE_DECODER,encoding="utf-8")
        output = root / "Unpack/v2.0.2/romfs/arc/data.trpfs"
        return {
            "repo": root, "workspace":root/"source", "output":output,
            "report":output/"_index/batches/pack-000003-000010.jsonl",
            "cache":root/"cache", "oodle":root/"oodle",
            "start": start, "end":end, "workers":workers,
            "pack_counts":[1]*13181,
            "command_prefix":[sys.executable, str(decoder)]
        }

    def test_real_multiprocess_merged_log_and_original_sha256(self):
        with tempfile.TemporaryDirectory() as directory:
            p = self._params(Path(directory))
            result = parallel.parallel_decode(**p)
            self.assertEqual(result["workers"], 4)
            self.assertEqual(result["records"], 8)
            self.assertEqual(result["failed"], 0)
            self.assertEqual([(x["startPack"],x["endPackExclusive"])
                              for x in result["workerRanges"]],
                             [(3,5),(5,7),(7,9),(9,11)])
            rows = [__import__("json").loads(s) for s in p["report"].read_text().splitlines()]
            self.assertEqual(len(rows),8)
            for i,row in enumerate(rows):
                payload = (f"payload-for-{i+3}").encode()
                output = p["output"]/"virtual"/row["Name"]
                self.assertEqual(output.read_bytes(),payload)
                self.assertEqual(parallel.sha256(output),row["Sha256"])
                self.assertEqual(row["OutputPath"],str(output.resolve()))
            # Re-extracting against existing identical files is safe;
            # changed native contents are rejected before overwrite.
            p["report"].unlink()
            rerun = parallel.parallel_decode(**p)
            self.assertEqual(rerun["records"],8)

    def test_conflicting_virtual_path_cannot_corrupt_shared_output(self):
        with tempfile.TemporaryDirectory() as directory:
            p = self._params(Path(directory),start=4,end=6,workers=2)
            saved=os.environ.get("ZA_TEST_COLLISION")
            os.environ["ZA_TEST_COLLISION"]="1"
            try:
                with self.assertRaisesRegex(RuntimeError,"conflicting output path"):
                    parallel.parallel_decode(**p)
            finally:
                if saved is None:
                    os.environ.pop("ZA_TEST_COLLISION",None)
                else:
                    os.environ["ZA_TEST_COLLISION"]=saved
            self.assertFalse(p["report"].exists())

    def test_incomplete_worker_cannot_publish(self):
        with tempfile.TemporaryDirectory() as directory:
            p = self._params(Path(directory),start=4,end=8,workers=2)
            p["pack_counts"][5]=2
            with self.assertRaisesRegex(RuntimeError,"native count mismatch"):
                parallel.parallel_decode(**p)
            self.assertFalse(p["report"].exists())

    def test_path_traversal_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for bad in ("../escape.bin","../","/absolute.bin","C:/windows.bin",
                        "bad\\name.bin","a//b.bin"):
                with self.assertRaises(ValueError):
                    parallel.safe_file(root,bad)


if __name__=="__main__":
    unittest.main()
