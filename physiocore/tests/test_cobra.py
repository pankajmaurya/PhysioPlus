import unittest
import os
import sys

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from physiocore.cobra_stretch import CobraStretchTracker


class TestCobraStretchTracker(unittest.TestCase):

    def test_cobra_video(self):
        tracker = CobraStretchTracker()
        
        # Override HOLD_SECS
        # tracker.hold_secs = 1.0
        
        # Override HOLD_SECS
        # tracker.hold_secs = 1.0

        # Get the path to the video file
        video_path = os.path.join(os.path.dirname(__file__), 'cobra-mini.mp4')
        
        # Process the video without displaying GUI
        count = tracker.process_video(video_path=video_path, display=False)
        # In development mode, try running with display ON too.
        # count = tracker.process_video(video_path=video_path, display=True)
        
        # Assert the count is 3
        self.assertEqual(count, 3)

if __name__ == '__main__':
    unittest.main()
