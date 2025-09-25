import unittest
import os
from physiocore.any_prone_straight_leg_raise import AnyProneSLRTracker

class TestAnyProneSLRTracker(unittest.TestCase):
    def test_any_prone_long_hold_video(self):
        tracker = AnyProneSLRTracker(test_mode=True)
        
        # Override HOLD_SECS
        display=False
        hold_secs = 6 if display else 4
        tracker.set_hold_secs(hold_secs)
        
        # Get the path to the video file
        video_path = os.path.join(os.path.dirname(__file__), 'prone-SLR-hold-4sec-pankaj1.mp4')
        
        # Process the video without displaying GUI
        count = tracker.process_video(video_path=video_path, display=False)
        self.assertEqual(count, 6)

if __name__ == '__main__':
    unittest.main()
