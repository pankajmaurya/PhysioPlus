import unittest
import os
from physiocore.shoulder_blade_squeeze import ShoulderBladeSqueezeTracker
from test_utils import compute_hold_duration

class TestShoulderBladeSqueezeTracker(unittest.TestCase):

    def test_shoulder_blade_squeeze_video(self):
        tracker = ShoulderBladeSqueezeTracker(test_mode=True)
        display = False
        hold_secs = compute_hold_duration(1.0, display)
        tracker.set_hold_secs(hold_secs)

        # Since there is no video for this exercise, we will just run it on an existing video
        # and expect the count to be 0
        video_path = os.path.join(os.path.dirname(__file__), 'cobra-mini.mp4')

        count = tracker.process_video(video_path=video_path, display=display)

        # Assert the count is 0 as the video does not contain the exercise
        self.assertEqual(count, 0)

if __name__ == '__main__':
    unittest.main()