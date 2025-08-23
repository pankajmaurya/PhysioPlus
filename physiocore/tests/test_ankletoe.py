import unittest
import os
from physiocore.ankle_toe_movement import AnkleToeMovementTracker

class TestAnkleToeMovementTracker(unittest.TestCase):

    def test_ankle_toe_video(self):
        tracker = AnkleToeMovementTracker()
        
        # Override HOLD_SECS for testing
        display=False
        tracker.hold_secs = 0.5 if display else 0.1
        
        # Get the path to the video file
        video_path = os.path.join(os.path.dirname(__file__), 'ankletoe.mp4')
        
        count = tracker.process_video(video_path=video_path, display=display)
        
        self.assertEqual(count, 2)

if __name__ == '__main__':
    unittest.main()
