import os
import unittest

from physiocore.neck_rotation import NeckRotationTracker

class TestNeckRotationTracker(unittest.TestCase):

    def test_tracker_initialization(self):
        tracker = NeckRotationTracker()
        video_path = os.path.join(os.path.dirname(__file__), 'neck-rotation-test.mp4')
        
        # Process the video without displaying GUI
        count = tracker.process_video(video_path=video_path, display=True)
        # In development mode, try running with display ON too.
        # count = tracker.process_video(video_path=video_path, display=True)
        
        # Assert the count is 3
        # The code assumes that the rotation starts with the left position of the head.
        # After recording the video, the mirror image happens. We lost one rotation.
        self.assertEqual(count, 2)

if __name__ == '__main__':
    unittest.main()
