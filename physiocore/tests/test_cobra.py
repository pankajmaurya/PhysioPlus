import unittest
import os
from physiocore.cobra_stretch import CobraStretchTracker

class TestCobraStretchTracker(unittest.TestCase):

    def test_cobra_video(self):
        tracker = CobraStretchTracker()
        display = False 
        # Override HOLD_SECS
        tracker.hold_secs = 0.1 if not display else 1.0
        
        # Get the path to the video file
        video_path = os.path.join(os.path.dirname(__file__), 'cobra-mini.mp4')
        
        count = tracker.process_video(video_path=video_path, display=display)
        
        # Assert the count is 3
        self.assertEqual(count, 3)

if __name__ == '__main__':
    unittest.main()
