import unittest
import os
from physiocore.any_prone_straight_leg_raise import AnyProneSLRTracker
from test_utils import compute_hold_duration

class TestAnyProneSLRTracker(unittest.TestCase):

    def test_any_prone_video(self):
        tracker = AnyProneSLRTracker(test_mode=True)
        
        # Override HOLD_SECS
        display=False
        hold_secs = compute_hold_duration(1, display, no_display_value=0.1)
        tracker.set_hold_secs(hold_secs)
        
        # Get the path to the video file
        video_path = os.path.join(os.path.dirname(__file__), 'prone-mini-test.mp4')
        
        # Process the video without displaying GUI
        count = tracker.process_video(video_path=video_path, display=False)
        # In development mode, try running with display ON too.
        # count = tracker.process_video(video_path=video_path, display=True)
        
        # Assert the count is 2
        self.assertEqual(count, 2)

if __name__ == '__main__':
    unittest.main()
