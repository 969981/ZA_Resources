#!/usr/bin/env python3
"""Independent checks for the mathematics observed in Z-A 2.0.2 ARM64.

The arithmetic below is transcribed from main+0xE5D1E8 and main+0xE5D244.
Tests do not emulate or prove the upstream Encounter.rare branch or live state.
"""
import random
import unittest


def za_shiny_predicate(tid_sid32, pid32):
    value = (tid_sid32 ^ pid32) & 0xFFFFFFFF
    return ((value & 0xFFF0) ^ (value >> 16)) < 16


def standard_xor_predicate(tid_sid32, pid32):
    x = (tid_sid32 ^ pid32) & 0xFFFFFFFF
    return ((x ^ (x >> 16)) & 0xFFFF) < 16


def za_mode_classifier(tid_sid32, pid32, version_byte, event_flag):
    # main+0xE5D244 from independently disassembled ARM64; 0 = normal,
    # 1/2 = two special subcategories. Naming 1/2 as star/square
    # without contextual validation would be unjustified.
    x = (tid_sid32 ^ pid32) & 0xFFFFFFFF
    xor_value = (x & 0xFFF0) ^ (x >> 16)
    if xor_value >= 16:
        return 0
    equals_halves = ((x >> 16) == (x & 0xFFFF))
    special = equals_halves or (version_byte == 0x22) or (event_flag & 1) != 0
    return 2 if special else 1


class ZAARM64ShinyArithmetic(unittest.TestCase):
    def test_standard_equivalence_exhaustive_xor_low_16(self):
        # Expected XOR result does not depend on the trainer ID value
        # beyond TID^PID; test full 16-bit lower half.
        trainer = 0
        for pid in range(0x10000):
            self.assertEqual(za_shiny_predicate(trainer, pid),
                             standard_xor_predicate(trainer, pid))

    def test_standard_equivalence_random_32bit(self):
        rng = random.Random(0x2A0202)
        for _ in range(25000):
            tr = rng.getrandbits(32)
            pid = rng.getrandbits(32)
            self.assertEqual(za_shiny_predicate(tr, pid),
                             standard_xor_predicate(tr, pid))

    def test_mode_classifications(self):
        tid = 0x12345678
        self.assertEqual(za_mode_classifier(tid, tid, 0, 0), 2)
        self.assertEqual(za_mode_classifier(tid, tid ^ 1, 0, 0), 1)
        self.assertEqual(za_mode_classifier(tid, tid ^ 1, 0x22, 0), 2)
        self.assertEqual(za_mode_classifier(tid, tid ^ 1, 0, 1), 2)
        self.assertEqual(za_mode_classifier(tid, tid ^ 0x100, 0, 0), 0)


if __name__ == "__main__":
    unittest.main()
