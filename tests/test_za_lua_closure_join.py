"""Synthetic checks for native ZA root closure / field-call evidence join.

No game data, external dependencies or original symbol-name assumptions.
"""
import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/Join-ZA-Lua-ClosureCalls.py"
SPEC = importlib.util.spec_from_file_location("za_closure_join", SCRIPT)
assert SPEC and SPEC.loader
JOIN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(JOIN)


def write_tsv(path, fieldnames, records):
    with path.open("w", encoding="utf-8", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(records)


class ClosureCallsJoinTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.f = [{
            "source": "event_ik", "class_hash": "C" + "1" * 16,
            "function_hash": "F" + "2" * 16, "root_pc": "50",
            "assignment_pc": "57", "child_proto_id": "8",
        }]
        self.s = [{
            "source": "event_ik", "class_hash": "C" + "3" * 16,
            "s_hash": "S" + "4" * 16, "root_pc": "60",
            "settable_pc": "64", "closure_proto_id": "9",
        }]
        self.calls = [
            self.call("event_ik", "8", "0", "S" + "5" * 16, "4", "6"),
            self.call("event_ik", "9", "0", "S" + "6" * 16, "2", "3"),
            self.call("main", "8", "0", "S" + "7" * 16, "1", "2"),
            self.call("event_ik", "11", "9", "S" + "8" * 16, "1", "3"),
        ]
        self.save()

    @staticmethod
    def call(source, proto, parent, digest, field_pc, call_pc):
        return {
            "source": source, "hash_token": digest, "proto_id": proto,
            "parent_proto_id": parent, "field_pc": field_pc,
            "field_offset_hex": "0x10", "call_pc": call_pc,
            "call_offset_hex": "0x18", "field_opcode": "GETFIELD",
        }

    def save(self):
        write_tsv(self.root / JOIN.INPUTS[0],
                  ("source", "class_hash", "function_hash", "root_pc",
                   "assignment_pc", "child_proto_id"), self.f)
        write_tsv(self.root / JOIN.INPUTS[1],
                  ("source", "class_hash", "s_hash", "root_pc",
                   "settable_pc", "closure_proto_id"), self.s)
        write_tsv(self.root / JOIN.INPUTS[2],
                  ("source", "hash_token", "proto_id", "parent_proto_id",
                   "field_pc", "field_offset_hex", "call_pc", "call_offset_hex",
                   "field_opcode"), self.calls)

    def test_source_scoped_and_kind_scoped_join(self):
        files, summary = JOIN.build(self.root)
        self.assertEqual(summary["matched_root_closure_calls"], 2)
        self.assertEqual(summary["matched_distinct_proto_keys"], 2)
        self.assertEqual(summary["unmatched_nested_proto_calls"], 1)
        self.assertEqual(summary["unmatched_root_or_other_calls"], 1)
        self.assertEqual(summary["matched_owner_kinds"], {"F": 1, "S": 1})
        self.assertEqual(summary["class_method_called_hash_groups"], 2)
        rows = list(csv.DictReader(files[JOIN.DETAIL].splitlines(), delimiter="\t"))
        self.assertEqual(rows[0]["owner_class_hash"], "C" + "1" * 16)
        self.assertEqual(rows[1]["owner_kind"], "S")
        self.assertEqual(rows[2]["owner_class_hash"], "")
        self.assertEqual(rows[3]["join_status"], "UNMATCHED_NESTED_PROTO")
        self.assertTrue(all(row["receiver_identity_confirmed"] == "NO" for row in rows))
        self.assertEqual(summary["original_names_recovered"], 0)

    def test_duplicate_root_proto_is_rejected(self):
        self.s[0]["closure_proto_id"] = "8"
        self.save()
        with self.assertRaisesRegex(ValueError, "Ambiguous"):
            JOIN.build(self.root)

    def test_wrong_parent_rejected(self):
        self.calls[0]["parent_proto_id"] = "100"
        self.save()
        with self.assertRaisesRegex(ValueError, "non-root parent"):
            JOIN.build(self.root)

    def test_duplicate_native_field_call_rejected(self):
        self.calls.append(self.calls[0].copy())
        self.save()
        with self.assertRaisesRegex(ValueError, "Duplicate native"):
            JOIN.build(self.root)

    def test_bad_hash_rejected(self):
        self.calls[0]["hash_token"] = "NOT_HASH"
        self.save()
        with self.assertRaisesRegex(ValueError, "Malformed"):
            JOIN.build(self.root)


if __name__ == "__main__":
    unittest.main()
