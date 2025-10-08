import unittest
import os
from physiocore.ankle_toe_movement import AnkleToeMovementTracker
from test_utils import compute_hold_duration

class TestAnkleToeMovementTracker(unittest.TestCase):

    def test_ankle_toe_video(self):
        tracker = AnkleToeMovementTracker(test_mode=True)
        
        # Override HOLD_SECS for testing
        display=False
        hold_secs = compute_hold_duration(0.5, display)
        tracker.set_hold_secs(hold_secs)
        
        # Get the path to the video file
        video_path = os.path.join(os.path.dirname(__file__), 'ankletoe.mp4')
        
        count = tracker.process_video(video_path=video_path, display=display)
        
        self.assertEqual(count, 2)

if __name__ == '__main__':
    unittest.main()