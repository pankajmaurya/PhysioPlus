import unittest
import os
from physiocore.bridging import BridgingTracker

class TestBridgingTracker(unittest.TestCase):

    def test_bridging_video(self):
        tracker = BridgingTracker()
        
        # Override HOLD_SECS
        # TODO: Investigate why override needed with display off mode
        tracker.hold_secs = 0.1
        
        # Get the path to the video file
        video_path = os.path.join(os.path.dirname(__file__), 'bridging.mp4')
        
        # Process the video without displaying GUI
        tracker.video = video_path
        tracker.start(display=False)
        tracker.thread.join()
        
        # Assert the count is 1
        self.assertEqual(tracker.count, 1)

if __name__ == '__main__':
    unittest.main()
