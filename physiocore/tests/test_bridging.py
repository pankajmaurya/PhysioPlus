import unittest
from physiocore.bridging import BridgingTracker

class TestBridgingTracker(unittest.TestCase):
    def test_bridging_video(self):
        tracker = BridgingTracker(test_mode=True)
        count = tracker.process_video('physiocore/tests/bridging.mp4')
        self.assertEqual(count, 1)

if __name__ == '__main__':
    unittest.main()
