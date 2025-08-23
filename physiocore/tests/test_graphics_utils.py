import unittest
from unittest.mock import MagicMock, patch
import numpy as np
import cv2

from physiocore.lib.graphics_utils import (
    get_default_drawing_specs,
    get_drawing_specs,
    ExerciseInfoRenderer,
    ExerciseState
)


class TestGraphicsUtils(unittest.TestCase):

    def test_get_default_drawing_specs_all(self):
        custom_connections, custom_style, connection_spec = get_default_drawing_specs('all')
        self.assertIsInstance(custom_connections, list)
        self.assertIsInstance(custom_style, dict)
        self.assertIsNotNone(connection_spec)
        # In 'all' mode, no landmarks should be excluded
        for landmark in custom_style.keys():
            self.assertNotEqual(custom_style[landmark].circle_radius, 0)

    def test_get_default_drawing_specs_default(self):
        custom_connections, custom_style, connection_spec = get_default_drawing_specs('default')
        self.assertIsInstance(custom_connections, list)
        self.assertIsInstance(custom_style, dict)
        self.assertIsNotNone(connection_spec)
        # In default mode, some landmarks should be excluded
        excluded_landmarks = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 17, 18, 19, 20, 21, 22]
        for landmark_idx in excluded_landmarks:
            self.assertEqual(custom_style[landmark_idx].circle_radius, 0)

    def test_get_drawing_specs(self):
        landmark_color = (0, 0, 255)
        connection_color = (0, 255, 0)
        landmark_thickness = 10
        connection_thickness = 20
        landmark_radius = 30
        connection_radius = 40
        excluded_landmarks = [11, 12]

        custom_connections, custom_style, connection_spec = get_drawing_specs(
            landmark_color, connection_color, landmark_thickness,
            connection_thickness, landmark_radius, connection_radius,
            excluded_landmarks
        )

        self.assertIsInstance(custom_connections, list)
        self.assertIsInstance(custom_style, dict)
        self.assertIsNotNone(connection_spec)

        self.assertEqual(connection_spec.color, connection_color)
        self.assertEqual(connection_spec.thickness, connection_thickness)

        for landmark_idx in excluded_landmarks:
            self.assertEqual(custom_style[landmark_idx].circle_radius, 0)

        # Check a non-excluded landmark
        self.assertEqual(custom_style[13].color, landmark_color)
        self.assertEqual(custom_style[13].thickness, landmark_thickness)
        self.assertEqual(custom_style[13].circle_radius, landmark_radius)

    def test_get_debug_color(self):
        renderer = ExerciseInfoRenderer()
        self.assertEqual(renderer._get_debug_color('angle'), (0, 255, 255))
        self.assertEqual(renderer._get_debug_color('pose'), (0, 255, 0))
        self.assertEqual(renderer._get_debug_color('lying'), (0, 255, 0))
        self.assertEqual(renderer._get_debug_color('ground'), (0, 255, 0))
        self.assertEqual(renderer._get_debug_color('orientation'), (0, 255, 0))
        self.assertEqual(renderer._get_debug_color('close'), (255, 255, 0))
        self.assertEqual(renderer._get_debug_color('near'), (255, 255, 0))
        self.assertEqual(renderer._get_debug_color('floored'), (255, 255, 0))
        self.assertEqual(renderer._get_debug_color('other'), (0, 255, 0))




if __name__ == '__main__':
    unittest.main()
