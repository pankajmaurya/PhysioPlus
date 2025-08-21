import unittest
import os
from physiocore.any_prone_straight_leg_raise import AnyProneSLRTracker

class TestAnyProneSLRTracker(unittest.TestCase):

    def test_any_prone_video(self):
        tracker = AnyProneSLRTracker()
        
        # Override HOLD_SECS
        tracker.hold_secs = 1.0
        
        # Get the path to the video file
        video_path = os.path.join(os.path.dirname(__file__), 'prone.mp4')
        
        # Process the video without displaying GUI
        count = tracker.process_video(video_path=video_path, display=False)
        # In development mode, try running with display ON too.
        # count = tracker.process_video(video_path=video_path, display=True)
        
        # Assert the count is 20
        self.assertEqual(count, 20)

if __name__ == '__main__':
    unittest.main()
