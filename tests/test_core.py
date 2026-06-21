"""Regression tests for the deterministic, non-GUI parts of MouseSign."""

import unittest

from core.text_to_trajectory import TextToTrajectory
from core.trajectory import TrajectoryGenerator


class TextToTrajectoryTests(unittest.TestCase):
    def test_english_hershey_glyph_is_available(self):
        converter = TextToTrajectory(allow_download=False)
        strokes = converter.text_to_strokes("Ada")
        self.assertTrue(strokes)
        self.assertTrue(all(len(stroke) >= 2 for stroke in strokes))

    def test_cached_chinese_character_is_available(self):
        converter = TextToTrajectory(allow_download=False)
        self.assertEqual(len(converter.get_chinese_character_trajectory("张")), 7)


class TrajectoryTests(unittest.TestCase):
    def test_normalization_keeps_signature_in_safe_canvas(self):
        generator = TrajectoryGenerator()
        trajectories = generator.generate_signature_trajectory(
            [[(10, 10), (20, 20), (30, 10)]]
        )
        trajectories = generator.apply_slant(trajectories, 20)
        normalized = generator.normalize_trajectory(trajectories)
        for trajectory in normalized:
            for x, y, _ in trajectory["points"]:
                self.assertGreaterEqual(x, 0)
                self.assertLessEqual(x, 1000)
                self.assertGreaterEqual(y, 0)
                self.assertLessEqual(y, 1000)


if __name__ == "__main__":
    unittest.main()
