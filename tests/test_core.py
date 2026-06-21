"""Regression tests for the deterministic, non-GUI parts of MouseSign."""

import unittest
from unittest.mock import patch

from core.hotkeys import EmergencyStopListener
from core.text_to_trajectory import TextToTrajectory
from core.trajectory import TrajectoryGenerator
from utils.bezier import BezierCurve
from utils.platform_utils import get_display_bounds


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
    def test_catmull_rom_passes_through_segment_endpoints(self):
        p0, p1, p2, p3 = (0, 0), (1, 2), (4, 3), (6, 0)
        self.assertEqual(BezierCurve.catmull_rom_spline(0, p0, p1, p2, p3), p1)
        self.assertEqual(BezierCurve.catmull_rom_spline(1, p0, p1, p2, p3), p2)

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


class PlatformUtilityTests(unittest.TestCase):
    def test_display_bounds_are_valid_rectangles(self):
        displays = get_display_bounds()
        self.assertTrue(displays)
        self.assertTrue(all(width > 0 and height > 0 for _, _, width, height in displays))

    def test_global_listener_is_disabled_on_macos(self):
        listener = EmergencyStopListener(lambda: None)
        with patch('core.hotkeys.platform.system', return_value='Darwin'):
            self.assertFalse(listener.start())


if __name__ == "__main__":
    unittest.main()
