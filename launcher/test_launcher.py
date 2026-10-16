"""Behavior checks for the menus and terminal resize handling."""

import unittest
import curses
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
        for key, view in [("1", "sources"), ("2", "manual"), ("3", "scenes"), ("4", "alarms"), ("5", "dsky")]:
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
            if key == "3":
                self.app.handle_key("\n")
            self.app.tick(1)
            before = (self.app.player.elapsed, self.app.demo.elapsed)
            self.app.handle_key(" ")
            self.app.tick(1)
            self.assertEqual((self.app.player.elapsed, self.app.demo.elapsed), before)
            if key == "4":
                self.app.handle_key("n")
                self.assertEqual(self.app.demo.elapsed, before[1] + 2)
            self.app.handle_key(" ")
            self.app.tick(1)
            self.assertNotEqual((self.app.player.elapsed, self.app.demo.elapsed), before)
            self.app.handle_key("\x1b")
            if key == "3":
                self.app.handle_key("\x1b")

    def test_scene_picker_launches_each_scene_and_preserves_its_selection_on_return(self):
        self.app.handle_key("3")
        for key in "1234567":
            self.app.handle_key(key)
            self.assertEqual(self.app.view, "scene")
            self.assertEqual(self.app.player.index, max(0, int(key) - 2))
            self.assertEqual(self.app.player.play_all, key == "1")
            self.app.handle_key("\x1b")
            self.assertEqual((self.app.view, self.app.scene_index), ("scenes", int(key) - 1))
        self.app.handle_key("\x1b")
        self.assertEqual(self.app.view, "menu")

    def test_paused_scene_supports_seek_replay_and_next_without_resuming(self):
        self.app.handle_key("3")
        self.app.handle_key("3")
        self.app.tick(1)
        self.app.handle_key(" ")
        self.app.handle_key("]")
        self.assertEqual(self.app.player.elapsed, 3)
        self.app.tick(2)
        self.assertEqual(self.app.player.elapsed, 3)
        self.app.handle_key("r")
        self.assertEqual(self.app.player.elapsed, 0)
        self.app.handle_key("l")
        self.assertEqual(self.app.player.scene.id, "landing")
        self.assertTrue(self.app.paused)
        self.app.handle_key(" ")
        self.app.tick(1)
        self.assertEqual(self.app.player.elapsed, 1)

    def test_pixel_colors_reuse_pairs_on_eight_color_terminals_and_handle_limits(self):
        self.app.color_enabled = True
        with patch("main.curses.COLORS", 8, create=True), patch("main.curses.COLOR_PAIRS", 16, create=True), patch("main.curses.init_pair") as init, patch("main.curses.color_pair", side_effect=lambda n: n * 256):
            first = self.app.color("pixel:red:white")
            same = self.app.color("pixel:red:metal")
            self.assertEqual(first, same)
            init.assert_called_once_with(1, 1, 7)
            self.app.next_color_pair = 16
            self.assertEqual(self.app.color("pixel:green:white"), self.app.styles["normal"])
            self.assertEqual(self.app.color("pixel:red:white"), first)

    def test_dsky_direct_keyboard_commands_pause_step_and_preserve_state_on_return(self):
        self.app.handle_key("5")
        for key in "V37 E 63 E ":
            self.app.handle_key(key)
        self.app.tick(10)
        self.assertEqual((self.app.dsky.program, self.app.dsky.elapsed), ("63", 10))
        self.app.handle_key("t")
        self.app.tick(5)
        self.assertEqual(self.app.dsky.elapsed, 10)
        self.app.handle_key("]")
        self.assertEqual(self.app.dsky.elapsed, 15)
        self.app.handle_key("\x1b")
        self.app.tick(5)
        self.app.handle_key("5")
        self.assertEqual(self.app.dsky.elapsed, 15)
        self.app.tick(1)
        self.assertEqual(self.app.dsky.elapsed, 16)

    def test_dsky_keypad_navigation_space_activation_and_enter_submission(self):
        self.app.handle_key("5")
        self.app.handle_key(" ")  # VERB is initially selected.
        for key in "35\n":
            self.app.handle_key(key)
        self.assertEqual(self.app.dsky.lamp_left, 5)
        self.app.handle_key(curses.KEY_UP)
        self.assertEqual(self.app.dsky_focus, 15)
        self.app.handle_key(" ")  # KEY REL
        self.assertFalse(self.app.dsky.editing)
        self.app.handle_key(curses.KEY_LEFT)
        self.app.handle_key(curses.KEY_DOWN)
        self.assertEqual(self.app.dsky_focus, 18)
        self.app.handle_key(curses.KEY_RIGHT)
        self.assertEqual(self.app.dsky_focus, 0)
        self.app.handle_key(" ")
        self.assertEqual(self.app.dsky.editing, "verb")

    def test_dsky_help_is_available_at_minimum_size_and_escape_closes_it(self):
        self.app.handle_key("5")
        self.app.handle_key("?")
        self.screen.height, self.screen.width = 24, 64
        self.app.draw()
        self.assertIn("V37 E 63 E", self.screen.output)
        self.app.handle_key("3")
        self.assertEqual(self.app.dsky.program, "00")
        self.app.handle_key("\x1b")
        self.assertEqual(self.app.view, "dsky")
        self.assertFalse(self.app.dsky_help)
        self.app.handle_key("\x1b")
        self.assertEqual(self.app.view, "menu")

    def test_all_views_fit_normal_narrow_and_tiny_terminal_sizes(self):
        for height, width in [(32, 110), (24, 64), (24, 110), (32, 64), (10, 30)]:
            self.screen.height, self.screen.width = height, width
            for view in ("menu", "sources", "files", "reader", "manual", "scenes", "scene", "alarms", "dsky"):
                with self.subTest(height=height, width=width, view=view):
                    self.app.view = view
                    self.app.draw()
                    self.assertTrue(self.screen.output)


if __name__ == "__main__":
    unittest.main()
