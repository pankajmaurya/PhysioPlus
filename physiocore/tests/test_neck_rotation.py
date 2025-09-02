import unittest
from physiocore.neck_rotation import NeckRotationTracker

class TestNeckRotationTracker(unittest.TestCase):

    def test_tracker_initialization(self):
        try:
            tracker = NeckRotationTracker()
            self.assertIsInstance(tracker, NeckRotationTracker)
        except Exception as e:
            self.fail(f"NeckRotationTracker initialization failed with an exception: {e}")

if __name__ == '__main__':
    unittest.main()
