import unittest
from unittest.mock import patch
from physiocore.lib.timer_utils import AdaptiveHoldTimer

class TestAdaptiveHoldTimer(unittest.TestCase):

    def test_initial_state(self):
        timer = AdaptiveHoldTimer(initial_hold_secs=3)
        self.assertEqual(timer.initial_hold_secs, 3)
        self.assertEqual(timer.adaptive_hold_secs, 3)
        self.assertFalse(timer.rep_in_progress)
        self.assertIsNone(timer.hold_start_time)
        self.assertFalse(timer.rep_counted_this_hold)

    @patch('time.time')
    def test_success_case(self, mock_time):
        # Setup
        mock_time.return_value = 1000
        timer = AdaptiveHoldTimer(initial_hold_secs=3)

        # Start the hold
        status = timer.update(in_hold_pose=True)
        self.assertTrue(timer.rep_in_progress)
        self.assertEqual(timer.hold_start_time, 1000)
        self.assertFalse(status["newly_counted_rep"])

        # Hold for 2 seconds (less than adaptive_hold_secs)
        mock_time.return_value = 1002
        status = timer.update(in_hold_pose=True)
        self.assertFalse(status["newly_counted_rep"])
        self.assertIsNotNone(status["status_text"])

        # Hold for 3 seconds (equal to adaptive_hold_secs)
        mock_time.return_value = 1003
        status = timer.update(in_hold_pose=True)
        self.assertTrue(status["newly_counted_rep"])
        self.assertTrue(timer.rep_counted_this_hold)

        # Hold for 4 seconds (longer than adaptive_hold_secs)
        mock_time.return_value = 1004
        status = timer.update(in_hold_pose=True)
        self.assertFalse(status["newly_counted_rep"]) # Should only count once

        # Release the pose
        status = timer.update(in_hold_pose=False)
        self.assertTrue(status["needs_reset"])
        self.assertFalse(timer.rep_in_progress)
        # Check that adaptive_hold_secs has increased
        # extra_hold = 4 - 3 = 1. adaptive_hold_secs += 1 * 0.5 = 3.5
        self.assertAlmostEqual(timer.adaptive_hold_secs, 3.5)

    @patch('time.time')
    def test_soft_failure_case(self, mock_time):
        # Setup
        mock_time.return_value = 1000
        timer = AdaptiveHoldTimer(initial_hold_secs=3)
        timer.adaptive_hold_secs = 5 # Simulate a previous successful rep

        # Start the hold
        timer.update(in_hold_pose=True)

        # Hold for 4 seconds (less than adaptive, but more than initial)
        mock_time.return_value = 1004
        status = timer.update(in_hold_pose=True)
        self.assertFalse(status["newly_counted_rep"])

        # Release the pose
        status = timer.update(in_hold_pose=False)
        self.assertTrue(status["needs_reset"])
        self.assertFalse(timer.rep_in_progress)
        # Check that adaptive_hold_secs has been lowered to the actual hold time
        self.assertAlmostEqual(timer.adaptive_hold_secs, 4)

    @patch('time.time')
    def test_hard_failure_case(self, mock_time):
        # Setup
        mock_time.return_value = 1000
        timer = AdaptiveHoldTimer(initial_hold_secs=3)
        timer.adaptive_hold_secs = 5 # Simulate a previous successful rep

        # Start the hold
        timer.update(in_hold_pose=True)

        # Hold for 2 seconds (less than initial)
        mock_time.return_value = 1002
        status = timer.update(in_hold_pose=True)
        self.assertFalse(status["newly_counted_rep"])

        # Release the pose
        status = timer.update(in_hold_pose=False)
        self.assertTrue(status["needs_reset"])
        self.assertFalse(timer.rep_in_progress)
        # Check that adaptive_hold_secs is unchanged
        self.assertAlmostEqual(timer.adaptive_hold_secs, 5)

if __name__ == '__main__':
    unittest.main()
