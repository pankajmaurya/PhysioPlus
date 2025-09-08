import unittest
import os
from physiocore.any_prone_straight_leg_raise import AnyProneSLRTracker

class TestAnyProneSLRTracker(unittest.TestCase):
    def test_any_prone_long_hold_video(self):
        tracker = AnyProneSLRTracker()
        
        # Override HOLD_SECS
        tracker.hold_secs = 8.0
        
        # Get the path to the video file
        video_path = os.path.join(os.path.dirname(__file__), 'prone-long-hold-2.mp4')
        
        # Process the video without displaying GUI
        count = tracker.process_video(video_path=video_path, display=False)
        self.assertEqual(count, 2)

if __name__ == '__main__':
    unittest.main()
