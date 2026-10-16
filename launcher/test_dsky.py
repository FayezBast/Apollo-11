"""Stateful checks for the DSKY keypad and scripted readings."""

import unittest

from dsky import Dsky, LAMPS, digits


def type_keys(panel, sequence):
    for key in sequence:
        panel.press({"V": "VERB", "N": "NOUN", "E": "ENTR"}.get(key, key))


class DskyTests(unittest.TestCase):
    def setUp(self):
        self.panel = Dsky()

    def start(self):
        type_keys(self.panel, "V37E63E")

    def test_lamp_test_lights_all_segments_then_restores_readings(self):
        before = self.panel.registers
        type_keys(self.panel, "V35E")
        self.assertTrue(all(self.panel.lit(lamp) for lamp in LAMPS))
        self.assertEqual(self.panel.field("program"), "88")
        self.assertEqual(self.panel.registers, ("+8888.8", "+8888.8", "+88888"))
        self.panel.advance(5)
        self.assertEqual(self.panel.registers, before)
        self.assertTrue(self.panel.lit("STBY"))
        self.assertFalse(self.panel.lit("TEMP"))

    def test_start_monitors_named_descent_data_and_idle_stops_it(self):
        self.start()
        self.assertEqual((self.panel.program, self.panel.verb, self.panel.noun), ("63", "16", "60"))
        self.assertEqual(self.panel.registers, ("+0520.0", "-0120.0", "+12500"))
        self.panel.advance(25)
        self.assertEqual(self.panel.registers, ("+0130.0", "-0060.0", "+02400"))
        type_keys(self.panel, "V37E00E")
        before = self.panel.registers
        self.panel.advance(20)
        self.assertEqual(self.panel.elapsed, 25)
        self.assertEqual(self.panel.registers, before)
        self.assertEqual(self.panel.phase, "P00 / STANDBY")

    def test_snapshot_holds_while_monitor_updates_and_n63_uses_total_speed(self):
        self.start()
        type_keys(self.panel, "V06N60E")
        before = self.panel.registers
        self.panel.advance(10)
        self.assertEqual(self.panel.registers, before)
        type_keys(self.panel, "V16N60E")
        self.assertNotEqual(self.panel.registers, before)
        horizontal = self.panel.registers[0]
        type_keys(self.panel, "V16N63E")
        self.assertGreater(float(self.panel.registers[0]), float(horizontal))
        self.assertIn("SPEED", self.panel.labels[0])

    def test_alarm_waits_for_pro_then_progresses_through_approach_contact(self):
        self.start()
        self.panel.advance(40)
        self.assertEqual(self.panel.elapsed, 35)
        self.assertTrue(self.panel.alert)
        self.assertTrue(self.panel.lit("PROG"))
        self.panel.advance(10)
        self.assertEqual(self.panel.elapsed, 35)
        self.panel.press("RSET")
        self.assertTrue(self.panel.alert)
        type_keys(self.panel, "V05N09E")
        self.assertEqual(self.panel.registers, ("01202", "00000", "00000"))
        self.panel.press("PRO")
        self.assertFalse(self.panel.lit("PROG"))
        self.assertTrue(self.panel.lit("RESTART"))
        self.panel.advance(10)
        self.assertEqual(self.panel.program, "64")
        self.panel.advance(25)
        self.assertEqual(self.panel.program, "66")
        type_keys(self.panel, "V16N60E")
        self.panel.advance(50)
        self.assertFalse(self.panel.running)
        self.assertEqual(self.panel.program, "00")
        self.assertEqual(self.panel.elapsed, 90)
        self.assertEqual(self.panel.registers, ("+0000.0", "+0000.0", "+00000"))
        self.assertIn("LANDED", self.panel.phase)

    def test_clock_rolls_over_without_displaying_sixty_seconds(self):
        type_keys(self.panel, "V16N65E")
        self.panel.advance(3599.999)
        self.assertEqual(self.panel.registers, ("+00000", "+00059", "+059.99"))
        self.panel.advance(.011)
        self.assertEqual(self.panel.registers, ("+00001", "+00000", "+000.01"))

    def test_incomplete_and_overlong_entries_can_be_corrected_and_cancelled(self):
        type_keys(self.panel, "V3E")
        self.assertTrue(self.panel.lit("OPR ERR"))
        self.assertEqual(self.panel.field("verb"), "3_")
        self.panel.press("RSET")
        self.panel.press("CLR")
        type_keys(self.panel, "357")
        self.assertEqual(self.panel.buffer, "35")
        self.assertTrue(self.panel.error)
        self.panel.press("BACKSPACE")
        type_keys(self.panel, "6E")
        self.assertEqual(self.panel.program, "00")  # V36 fresh start.
        self.assertFalse(self.panel.error)
        type_keys(self.panel, "N6")
        self.panel.press("KEYREL")
        self.assertFalse(self.panel.lit("KEY REL"))
        self.assertEqual(self.panel.field("noun"), "00")

    def test_invalid_program_or_verb_noun_does_not_change_active_telemetry(self):
        self.start()
        self.panel.advance(10)
        before = self.panel.registers
        for sequence in ("V37E99E", "V16N99E", "V05N60E", "V99E"):
            type_keys(self.panel, sequence)
            self.assertTrue(self.panel.error)
            self.assertEqual(self.panel.program, "63")
            self.assertEqual(self.panel.elapsed, 10)
            self.assertEqual(self.panel.registers, before)
        self.panel.press("RSET")
        self.assertFalse(self.panel.error)

    def test_fresh_start_clears_alarm_and_replay_can_trigger_it_again(self):
        self.start()
        self.panel.advance(35)
        type_keys(self.panel, "V36E")
        self.assertEqual((self.panel.elapsed, self.panel.clock), (0, 0))
        self.assertEqual(self.panel.alarms, [0, 0, 0])
        self.assertTrue(self.panel.lit("RESTART"))
        self.assertFalse(self.panel.running)
        self.start()
        self.panel.advance(35)
        self.assertTrue(self.panel.alert)

    def test_bad_time_steps_leave_state_unchanged(self):
        self.start()
        for seconds in (-1, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                self.panel.advance(seconds)
        self.panel.advance(0)
        self.assertEqual((self.panel.clock, self.panel.elapsed), (0, 0))

    def test_every_readout_renders_as_three_equal_width_segment_rows(self):
        for value in ("00", "6_", "+0520.0", "-0120.0", "+12500", "01202"):
            rows = digits(value)
            self.assertEqual(len(rows), 3)
            self.assertEqual(len({len(row) for row in rows}), 1)


if __name__ == "__main__":
    unittest.main()
