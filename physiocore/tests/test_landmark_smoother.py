import unittest
import mediapipe as mp
from mediapipe.framework.formats import landmark_pb2
import numpy as np

from physiocore.lib.landmark_smoother import LandmarkSmoother

def _create_landmark_list(num_landmarks, base_value=0.1):
    """Helper function to create a NormalizedLandmarkList."""
    landmarks = landmark_pb2.NormalizedLandmarkList()
    for i in range(num_landmarks):
        lm = landmarks.landmark.add()
        val = base_value * (i + 1)
        lm.x, lm.y, lm.z, lm.visibility, lm.presence = val, val, val, val, val
    return landmarks

class TestLandmarkSmoother(unittest.TestCase):

    def setUp(self):
        """Set up for each test."""
        self.smoother = LandmarkSmoother(alpha=0.5)
        self.landmarks1 = _create_landmark_list(3, base_value=0.1)
        self.landmarks2 = _create_landmark_list(3, base_value=0.2)

    def test_initialization(self):
        """Test that the smoother initializes correctly."""
        self.assertEqual(self.smoother.alpha, 0.5)
        self.assertIsNone(self.smoother.smoothed_landmarks)

    def test_first_call(self):
        """Test that the first call returns the original landmarks."""
        smoothed = self.smoother(self.landmarks1)
        self.assertEqual(smoothed, self.landmarks1)
        self.assertIsNotNone(self.smoother.smoothed_landmarks)
        self.assertEqual(self.smoother.smoothed_landmarks, self.landmarks1)

    def test_smoothing_logic(self):
        """Test the exponential moving average logic."""
        # First call to initialize
        self.smoother(self.landmarks1)

        # Second call
        smoothed2 = self.smoother(self.landmarks2)

        # Expected values: 0.5 * 0.2 + 0.5 * 0.1 = 0.15
        expected_val1 = 0.5 * (0.2 * 1) + 0.5 * (0.1 * 1)
        self.assertAlmostEqual(smoothed2.landmark[0].x, expected_val1, places=5)
        self.assertAlmostEqual(smoothed2.landmark[0].y, expected_val1, places=5)
        self.assertAlmostEqual(smoothed2.landmark[0].z, expected_val1, places=5)

        expected_val2 = 0.5 * (0.2 * 2) + 0.5 * (0.1 * 2)
        self.assertAlmostEqual(smoothed2.landmark[1].x, expected_val2, places=5)

    def test_smoothing_alpha_one(self):
        """Test smoothing with alpha=1 (output should be the same as input)."""
        self.smoother.alpha = 1.0
        self.smoother(self.landmarks1)
        smoothed2 = self.smoother(self.landmarks2)
        self.assertEqual(smoothed2, self.landmarks2)

    def test_smoothing_alpha_zero(self):
        """Test smoothing with alpha=0 (keeps previous value's coords)."""
        self.smoother.alpha = 0.0
        self.smoother(self.landmarks1)  # State is now landmarks1
        smoothed2 = self.smoother(self.landmarks2)

        # Coords should be from landmarks1
        for i in range(len(self.landmarks1.landmark)):
            self.assertAlmostEqual(smoothed2.landmark[i].x, self.landmarks1.landmark[i].x, places=5)
            self.assertAlmostEqual(smoothed2.landmark[i].y, self.landmarks1.landmark[i].y, places=5)
            self.assertAlmostEqual(smoothed2.landmark[i].z, self.landmarks1.landmark[i].z, places=5)

        # Visibility/presence should be from landmarks2
        for i in range(len(self.landmarks2.landmark)):
            self.assertAlmostEqual(smoothed2.landmark[i].visibility, self.landmarks2.landmark[i].visibility, places=5)
            self.assertAlmostEqual(smoothed2.landmark[i].presence, self.landmarks2.landmark[i].presence, places=5)

    def test_none_input(self):
        """Test that None input returns None."""
        self.assertIsNone(self.smoother(None))

    def test_reset(self):
        """Test that the reset method clears the state."""
        self.smoother(self.landmarks1)
        self.assertIsNotNone(self.smoother.smoothed_landmarks)
        self.smoother.reset()
        self.assertIsNone(self.smoother.smoothed_landmarks)
        # After reset, the next call should behave like the first call
        smoothed = self.smoother(self.landmarks2)
        self.assertEqual(smoothed, self.landmarks2)

    def test_visibility_and_presence_are_copied(self):
        """Test that visibility and presence are copied from the input."""
        self.smoother(self.landmarks1)
        smoothed2 = self.smoother(self.landmarks2)

        # Visibility and presence should be from landmarks2
        self.assertAlmostEqual(smoothed2.landmark[0].visibility, self.landmarks2.landmark[0].visibility)
        self.assertAlmostEqual(smoothed2.landmark[0].presence, self.landmarks2.landmark[0].presence)
        self.assertAlmostEqual(smoothed2.landmark[1].visibility, self.landmarks2.landmark[1].visibility)
        self.assertAlmostEqual(smoothed2.landmark[1].presence, self.landmarks2.landmark[1].presence)


if __name__ == '__main__':
    unittest.main()
