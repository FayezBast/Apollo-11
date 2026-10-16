"""Run with: python3 -m unittest discover -s launcher -p 'test_*.py'."""

import tempfile
import unittest
from pathlib import Path

from core import AlarmDemo, CATALOG, COMMANDS, read_source, source_files


class CatalogTests(unittest.TestCase):
    def test_menu_has_unique_working_destinations(self):
        self.assertEqual({entry[0] for entry in CATALOG}, {"sources", "manual", "scenes", "alarms"})
        self.assertEqual(len(CATALOG), len({entry[0] for entry in CATALOG}))

    def test_manual_points_to_real_source_lines(self):
        for code, _, keys, _, filename, line in COMMANDS:
            with self.subTest(code=code):
                source = read_source("Luminary099", filename)
                self.assertTrue(keys.startswith("VERB"))
                self.assertTrue(source[line - 1].startswith("#"))

    def test_explorer_reads_both_modules_and_rejects_other_paths(self):
        for module in ["Luminary099", "Comanche055"]:
            self.assertIn("MAIN.agc", source_files(module))
            self.assertGreater(len(read_source(module, "MAIN.agc")), 10)
        with self.assertRaises(ValueError):
            source_files("../")
        for filename in ["../LICENSE.md", "/etc/passwd", "missing.agc"]:
            with self.assertRaises(ValueError):
                read_source("Luminary099", filename)

    def test_explorer_rejects_a_symlink_leaving_the_module(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Luminary099").mkdir()
            (root / "outside.agc").write_text("outside")
            (root / "Luminary099" / "link.agc").symlink_to(root / "outside.agc")
            with self.assertRaises(ValueError):
                read_source("Luminary099", "link.agc", root)


class AlarmTests(unittest.TestCase):
    def test_each_single_load_is_stable(self):
        for radar, monitor in [(False, False), (True, False), (False, True)]:
            demo = AlarmDemo(radar=radar, monitor=monitor)
            demo.advance(60)
            self.assertEqual((demo.cores, demo.restarts), (1, 0))

    def test_core_exhaustion_restarts_and_sheds_the_monitor(self):
        demo = AlarmDemo(radar=True, monitor=True)
        demo.advance(14)
        self.assertEqual((demo.cores, demo.restarts), (8, 0))
        demo.advance(2)
        self.assertEqual((demo.last_alarm, demo.cores, demo.restarts), ("01202", 1, 1))
        self.assertTrue(demo.radar)
        self.assertFalse(demo.monitor)
        demo.advance(60)
        self.assertEqual(demo.restarts, 1)

    def test_shedding_load_before_exhaustion_releases_the_backlog(self):
        demo = AlarmDemo(radar=True, monitor=True)
        demo.select_pool(True)
        demo.advance(4)
        self.assertEqual((demo.cores, demo.vacs), (3, 3))
        demo.monitor = False
        demo.advance(2)
        self.assertEqual((demo.cores, demo.vacs, demo.restarts), (1, 1, 0))

    def test_vac_exhaustion_is_distinct_from_core_exhaustion(self):
        demo = AlarmDemo(radar=True, monitor=True)
        demo.select_pool(True)
        demo.advance(8)
        self.assertEqual((demo.vacs, demo.cores, demo.restarts), (5, 5, 0))
        demo.advance(2)
        self.assertEqual((demo.last_alarm, demo.vacs, demo.cores), ("01201", 1, 1))

    def test_bad_time_steps_are_rejected_and_zero_does_not_advance(self):
        demo = AlarmDemo()
        for seconds in [-1, 61, float("nan"), float("inf")]:
            with self.assertRaises(ValueError):
                demo.advance(seconds)
        demo.advance(0)
        self.assertEqual(demo.elapsed, 0)


if __name__ == "__main__":
    unittest.main()
