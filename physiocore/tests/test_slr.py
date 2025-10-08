import unittest
import os
from physiocore.any_straight_leg_raise import AnySLRTracker

class TestAnySLRTracker(unittest.TestCase):

    def test_slr_video(self):
        tracker = AnySLRTracker(test_mode=True)
        tracker.debug = True
        
        # Override HOLD_SECS for testing
        display = False
        hold_secs = 1 if display else 0.5
        tracker.set_hold_secs(hold_secs)
        
        # Get the path to the video file
        video_path = os.path.join(os.path.dirname(__file__), 'slr-mini.mp4')
        
        count = tracker.process_video(video_path=video_path, display=display)
        
        # Assert the count is 2
        self.assertEqual(count, 2)

if __name__ == '__main__':
    unittest.main()
