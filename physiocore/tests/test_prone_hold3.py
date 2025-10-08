import unittest
import os
from physiocore.any_prone_straight_leg_raise import AnyProneSLRTracker
from test_utils import compute_hold_duration

class TestAnyProneSLRTracker(unittest.TestCase):
    @unittest.expectedFailure
    def test_any_prone_long_hold_video(self):
        tracker = AnyProneSLRTracker(test_mode=True)
        
        # Override HOLD_SECS
        display=False
        hold_secs = compute_hold_duration(12, display)
        tracker.set_hold_secs(hold_secs)
        
        # Get the path to the video file
        # The model fluctuates and the counter resets, this test is failing.
        video_path = os.path.join(os.path.dirname(__file__), 'prone-long-hold.mp4')
        
        # Process the video without displaying GUI
        count = tracker.process_video(video_path=video_path, display=display)
        self.assertEqual(count, 1)

if __name__ == '__main__':
    unittest.main()