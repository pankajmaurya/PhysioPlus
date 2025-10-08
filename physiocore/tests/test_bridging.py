import unittest
import os
from physiocore.bridging import BridgingTracker
from test_utils import compute_hold_duration

class TestBridgingTracker(unittest.TestCase):

    def test_bridging_video(self):
        tracker = BridgingTracker(test_mode=True)
        
        # Override HOLD_SECS
        # TODO: Investigate why override needed with display off mode
        display=False
        hold_secs = compute_hold_duration(1.0, display)
        tracker.set_hold_secs(hold_secs)
        
        # Get the path to the video file
        video_path = os.path.join(os.path.dirname(__file__), 'bridging.mp4')
        
        # Process the video without displaying GUI
        count = tracker.process_video(video_path=video_path, display=display)
        # In development mode, try running with display ON too.
        # count = tracker.process_video(video_path=video_path, display=True)
        
        # Assert the count is 1
        self.assertEqual(count, 1)

if __name__ == '__main__':
    unittest.main()