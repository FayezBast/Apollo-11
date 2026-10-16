"""Playback and visual-state checks for the original scene collection."""

import unittest

from scenes import Canvas, PIXEL_COLORS, SCENES, ScenePlayer, flag, render_scene


class PlaybackTests(unittest.TestCase):
    def test_orbit_loops_but_finite_scenes_hold_at_their_ending(self):
        player = ScenePlayer()
        player.advance(SCENES[0].duration + 2)
        self.assertEqual(player.elapsed, 2)
        self.assertFalse(player.finished)
        for index in range(1, len(SCENES)):
            player.select(index)
            player.advance(player.scene.duration)
            before = render_scene(index, player.elapsed, 74, 20)[0].plain()
            player.advance(100)
            self.assertTrue(player.finished)
            self.assertEqual(before, render_scene(index, player.elapsed, 74, 20)[0].plain())

    def test_full_show_carries_elapsed_time_through_scene_boundaries_then_stops(self):
        player = ScenePlayer()
        player.select(0, play_all=True)
        player.advance(SCENES[0].duration + 0.25)
        self.assertEqual((player.index, player.elapsed), (1, 0.25))
        player.advance(sum(scene.duration for scene in SCENES))
        self.assertEqual(player.index, len(SCENES) - 1)
        self.assertEqual(player.elapsed, player.scene.duration)
        self.assertTrue(player.finished)
        self.assertIn("CREW ABOARD", render_scene(player.index, player.elapsed, 74, 20)[1])

    def test_seek_stays_in_the_selected_scene_and_is_bounded(self):
        player = ScenePlayer()
        player.select(2, play_all=True)
        player.seek(-100)
        self.assertEqual((player.index, player.elapsed), (2, 0))
        player.seek(100)
        self.assertEqual((player.index, player.elapsed), (2, SCENES[2].duration))
        player.seek(-2)
        self.assertEqual(player.elapsed, SCENES[2].duration - 2)

    def test_invalid_selections_and_nonfinite_times_are_rejected(self):
        player = ScenePlayer()
        for index in [-1, len(SCENES)]:
            with self.assertRaises(ValueError):
                player.select(index)
        for seconds in [-1, float("nan"), float("inf")]:
            with self.assertRaises(ValueError):
                player.advance(seconds)
        for seconds in [float("nan"), float("inf")]:
            with self.assertRaises(ValueError):
                player.seek(seconds)


class ArtworkTests(unittest.TestCase):
    def test_all_scenes_animate_and_replay_the_same_frame(self):
        for index, scene in enumerate(SCENES):
            with self.subTest(scene=scene.id):
                start, _ = render_scene(index, 0, 74, 20)
                middle, caption = render_scene(index, scene.duration * 0.35, 74, 20)
                replay, _ = render_scene(index, scene.duration * 0.35, 74, 20)
                self.assertNotEqual(start.cells, middle.cells)
                self.assertEqual(middle.cells, replay.cells)
                self.assertTrue(caption)

    def test_contact_switches_the_engine_off_at_touchdown(self):
        burning, approach = render_scene(2, 3, 74, 20)
        landed, contact = render_scene(2, SCENES[2].duration, 74, 20)
        self.assertTrue(any("flame" in style for row in burning.cells for _, style in row))
        self.assertFalse(any("flame" in style for row in landed.cells for _, style in row))
        self.assertNotIn("CONTACT", approach)
        self.assertIn("CONTACT", contact)
        self.assertIn("ARZI", landed.plain())

    def test_moonwalk_plants_the_flag_and_returns_the_crew(self):
        leaving, _ = render_scene(4, 0, 74, 20)
        planted, _ = render_scene(4, SCENES[4].duration * 0.7, 74, 20)
        self.assertFalse(any("pixel:red:red" == style for row in leaving.cells for _, style in row))
        self.assertTrue(any("pixel:red:red" == style for row in planted.cells for _, style in row))
        self.assertTrue(any("green" in style for row in planted.cells for _, style in row))
        final, caption = render_scene(4, SCENES[4].duration, 74, 20)
        self.assertIn("CREW SAFELY ABOARD", caption)
        self.assertIn("ARZI", final.plain())

    def test_moonhop_collects_stars_then_raises_the_flag_and_boards(self):
        self.assertIn("STARS 0 / 3", render_scene(5, 0, 74, 20)[1])
        self.assertIn("STARS 3 / 3", render_scene(5, SCENES[5].duration * 0.61, 74, 20)[1])
        self.assertIn("RAISE", render_scene(5, SCENES[5].duration * 0.75, 74, 20)[1])
        self.assertIn("CREW ABOARD", render_scene(5, SCENES[5].duration, 74, 20)[1])

    def test_pixel_layers_preserve_the_other_half_of_a_terminal_cell(self):
        frame = Canvas(2, 1)
        frame.pixel(0, 0, "red")
        frame.pixel(0, 1, "white")
        self.assertEqual(frame.cells[0][0], ("▀", "pixel:red:white"))
        frame.pixel(0, 0, "green")
        self.assertEqual(frame.cells[0][0], ("▀", "pixel:green:white"))
        before = [row[:] for row in frame.cells]
        frame.pixel(-1, 0, "red")
        frame.pixel(2, 1, "red")
        self.assertEqual(frame.cells, before)

    def test_lebanese_flag_has_red_bands_white_center_and_a_green_cedar(self):
        frame = Canvas(30, 15)
        flag(frame, 5, 12)
        top = 12 * 2 - 20
        rows = []
        for y in range(top, top + 8):
            rows.append([frame.cells[y // 2][x][1].split(":")[1 + y % 2] for x in range(6, 18)])
        self.assertTrue(all(color == "red" for row in rows[:2] + rows[6:] for color in row))
        self.assertEqual([row.count("green") for row in rows[2:6]], [2, 4, 6, 2])
        self.assertTrue(all(color in {"white", "green"} for row in rows[2:6] for color in row))

    def test_planting_unfurls_then_salutes_and_leaves_the_lebanese_flag_up(self):
        duration = SCENES[4].duration
        stages = [render_scene(4, duration * t, 74, 20) for t in [.32, .44, .6, 1]]
        self.assertIn("pole", stages[0][1])
        self.assertIn("Unfurl", stages[1][1])
        self.assertIn("LEBANESE FLAG", stages[2][1])
        self.assertIn("LEBANESE FLAG PLANTED", stages[3][1])
        red_counts = [sum("red" in style for row in frame.cells for _, style in row) for frame, _ in stages]
        self.assertLess(red_counts[1], red_counts[2])
        self.assertGreater(red_counts[3], 10)

    def test_touchdown_has_a_shutdown_and_settling_phase(self):
        duration = SCENES[2].duration
        shutdown, first = render_scene(2, duration * .7, 74, 20)
        quiet, last = render_scene(2, duration, 74, 20)
        self.assertIn("SHUTTING DOWN", first)
        self.assertIn("QUIET", last)
        self.assertNotEqual(shutdown.cells, quiet.cells)

    def test_every_frame_fits_small_stages_and_has_renderable_color_runs(self):
        for width, height in [(58, 12), (104, 20), (43, 10)]:
            for index, scene in enumerate(SCENES):
                for fraction in [0, 0.25, 0.5, 0.75, 1]:
                    with self.subTest(size=(width, height), scene=scene.id, fraction=fraction):
                        frame, _ = render_scene(index, scene.duration * fraction, width, height)
                        self.assertEqual(len(frame.cells), height)
                        self.assertTrue(all(len(row) == width for row in frame.cells))
                        for x, y, text, style in frame.runs():
                            self.assertTrue(0 <= y < height)
                            self.assertTrue(0 <= x < width and x + len(text) <= width)
                            if style.startswith("pixel:"):
                                for color in style.split(":")[1:]:
                                    self.assertIn(color, PIXEL_COLORS)
                            else:
                                self.assertIn(style, {"normal", "dim", "accent", "cyan", "error"})
        with self.assertRaises(ValueError):
            Canvas(0, 10)


if __name__ == "__main__":
    unittest.main()
