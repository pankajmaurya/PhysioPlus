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
        
        tracker.video = video_path
        tracker.start(display=False)
        tracker.thread.join()
        
        self.assertEqual(tracker.count, 2)

if __name__ == '__main__':
    unittest.main()
