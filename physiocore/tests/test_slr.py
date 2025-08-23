import unittest
import os
from physiocore.any_straight_leg_raise import AnySLRTracker

class TestAnySLRTracker(unittest.TestCase):

    def test_slr_video(self):
        tracker = AnySLRTracker()
        tracker.debug = True
        
        # Override HOLD_SECS for testing
        display = False
        tracker.hold_secs = 1.0 if display else 0.5
        
        # Get the path to the video file
        video_path = os.path.join(os.path.dirname(__file__), 'slr-mini.mp4')
        
        count = tracker.process_video(video_path=video_path, display=display)
        
        # Assert the count is 2
        self.assertEqual(count, 2)

if __name__ == '__main__':
    unittest.main()
