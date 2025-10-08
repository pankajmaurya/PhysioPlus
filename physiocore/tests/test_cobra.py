import unittest
import os
from physiocore.cobra_stretch import CobraStretchTracker
from test_utils import compute_hold_duration

class TestCobraStretchTracker(unittest.TestCase):

    def test_cobra_video(self):
        tracker = CobraStretchTracker(test_mode=True)
        display = False 
        # Override HOLD_SECS
        hold_secs = compute_hold_duration(1.0, display)
        tracker.set_hold_secs(hold_secs)
        
        # Get the path to the video file
        video_path = os.path.join(os.path.dirname(__file__), 'cobra-mini.mp4')
        
        count = tracker.process_video(video_path=video_path, display=display)
        
        # Assert the count is 3
        self.assertEqual(count, 3)

if __name__ == '__main__':
    unittest.main()