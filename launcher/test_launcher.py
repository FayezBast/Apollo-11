"""Behavior checks for the menus and terminal resize handling."""

import unittest
from unittest.mock import patch

from main import Launcher


class Screen:
    def __init__(self, height=32, width=110):
        self.height, self.width = height, width
        self.output = []

    def getmaxyx(self):
        return self.height, self.width

    def erase(self):
        self.output.clear()

    def refresh(self):
        pass

    def addnstr(self, y, x, text, length, style):
        if not (0 <= y < self.height and 0 <= x < self.width and length <= self.width - x - 1):
            raise AssertionError("Draw outside terminal")
        self.output.append(text[:length])


class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.screen = Screen()
        self.app = Launcher(self.screen)

    def test_every_menu_destination_opens_returns_and_quit_exits(self):
        for key, view in [("1", "sources"), ("2", "manual"), ("3", "scene"), ("4", "alarms")]:
            self.app.handle_key(key)
            self.assertEqual(self.app.view, view)
            self.app.handle_key("q")
            self.assertEqual(self.app.view, "menu")
            self.assertTrue(self.app.alive)
        self.app.handle_key("q")
        self.assertFalse(self.app.alive)

    def test_manual_opens_the_original_listing_and_returns_to_selected_command(self):
        self.app.handle_key("2")
        self.app.handle_key("j")
        self.app.handle_key("\n")
        self.assertEqual(self.app.view, "reader")
        self.assertIn("CHANGE PROGRAM", self.app.lines[self.app.scroll])
        self.app.handle_key("\x1b")
        self.assertEqual((self.app.view, self.app.manual_index), ("manual", 1))

    def test_uppercase_shortcuts_work_without_changing_source_search_text(self):
        self.app.handle_key("J")
        self.assertEqual(self.app.menu_index, 1)
        self.app.handle_key("\n")
        self.assertEqual(self.app.view, "manual")
        self.app.handle_key("B")
        self.assertEqual(self.app.view, "menu")

    def test_source_filter_handles_no_matches_and_opens_a_real_file(self):
        self.app.handle_key("1")
        self.app.handle_key("\n")
        self.app.handle_key("/")
        for key in "not-a-real-file":
            self.app.handle_key(key)
        self.app.handle_key("\n")
        self.app.handle_key("\n")
        self.assertEqual(self.app.view, "files")
        self.app.handle_key("/")
        self.app.handle_key("\x1b")
        self.app.handle_key("/")
        for key in "MAIN.agc":
            self.app.handle_key(key)
        self.app.handle_key("\n")
        self.app.handle_key("\n")
        self.assertEqual(self.app.source_name, "Luminary099/MAIN.agc")
        self.app.handle_key("\x1b")
        self.assertEqual(self.app.view, "files")

    def test_missing_source_reports_error_without_leaving_the_manual(self):
        self.app.handle_key("2")
        with patch("main.read_source", side_effect=OSError("file removed")):
            self.app.handle_key("\n")
        self.assertEqual(self.app.view, "manual")
        self.assertIn("file removed", self.app.status)

    def test_pause_preserves_animation_and_alarm_time_then_step_and_resume_work(self):
        for key in ("3", "4"):
            self.app.handle_key(key)
            self.app.tick(1)
            before = (self.app.scene_time, self.app.demo.elapsed)
            self.app.handle_key(" ")
            self.app.tick(1)
            self.assertEqual((self.app.scene_time, self.app.demo.elapsed), before)
            if key == "4":
                self.app.handle_key("n")
                self.assertEqual(self.app.demo.elapsed, before[1] + 2)
            self.app.handle_key(" ")
            self.app.tick(1)
            self.assertNotEqual((self.app.scene_time, self.app.demo.elapsed), before)
            self.app.handle_key("\x1b")

    def test_all_views_fit_normal_narrow_and_tiny_terminal_sizes(self):
        for height, width in [(32, 110), (24, 64), (10, 30)]:
            self.screen.height, self.screen.width = height, width
            for view in ("menu", "sources", "files", "reader", "manual", "scene", "alarms"):
                with self.subTest(height=height, width=width, view=view):
                    self.app.view = view
                    self.app.draw()
                    self.assertTrue(self.screen.output)


if __name__ == "__main__":
    unittest.main()
