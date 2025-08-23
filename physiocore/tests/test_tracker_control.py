import unittest
import time
from physiocore.ankle_toe_movement import AnkleToeMovementTracker
from physiocore.bridging import BridgingTracker
from physiocore.cobra_stretch import CobraStretchTracker
from physiocore.any_straight_leg_raise import AnySLRTracker
from physiocore.any_prone_straight_leg_raise import AnyProneSLRTracker

class TestTrackerControl(unittest.TestCase):

    def _test_tracker(self, tracker_class, video_path):
        tracker = tracker_class()
        tracker.video = video_path
        tracker.start(display=False)
        self.assertIsNotNone(tracker.thread)
        self.assertTrue(tracker.thread.is_alive())
        self.assertTrue(tracker.running)

        time.sleep(1) # Let the tracker run for a bit

        tracker.stop()
        tracker.thread.join()
        # After calling stop, the thread should not be alive
        self.assertFalse(tracker.thread.is_alive())
        self.assertFalse(tracker.running)

    def test_ankle_toe_movement_tracker_control(self):
        self._test_tracker(AnkleToeMovementTracker, 'physiocore/tests/ankletoe.mp4')

    def test_bridging_tracker_control(self):
        self._test_tracker(BridgingTracker, 'physiocore/tests/bridging.mp4')

    def test_cobra_stretch_tracker_control(self):
        self._test_tracker(CobraStretchTracker, 'physiocore/tests/cobra-mini.mp4')

    def test_any_slr_tracker_control(self):
        self._test_tracker(AnySLRTracker, 'physiocore/tests/slr-mini.mp4')

    def test_any_prone_slr_tracker_control(self):
        self._test_tracker(AnyProneSLRTracker, 'physiocore/tests/prone-mini-test.mp4')

if __name__ == '__main__':
    unittest.main()
