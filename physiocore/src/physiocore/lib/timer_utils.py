import time

class AdaptiveHoldTimer:
    def __init__(self, initial_hold_secs):
        self.initial_hold_secs = initial_hold_secs
        self.adaptive_hold_secs = initial_hold_secs
        self.rep_in_progress = False
        self.hold_start_time = None
        self.rep_counted_this_hold = False

    def update(self, in_hold_pose):
        newly_counted_rep = False
        status_text = None
        needs_reset = False

        if in_hold_pose:
            if not self.rep_in_progress:
                self.rep_in_progress = True
                self.hold_start_time = time.time()
                self.rep_counted_this_hold = False
            else:
                hold_duration = time.time() - self.hold_start_time
                remaining_time = self.adaptive_hold_secs - hold_duration
                if remaining_time > 0:
                    status_text = f'hold pose: {remaining_time:.2f}'

                if hold_duration >= self.adaptive_hold_secs and not self.rep_counted_this_hold:
                    newly_counted_rep = True
                    self.rep_counted_this_hold = True
        else:
            if self.rep_in_progress:
                actual_hold_time = time.time() - self.hold_start_time

                if actual_hold_time >= self.adaptive_hold_secs:
                    extra_hold = actual_hold_time - self.adaptive_hold_secs
                    self.adaptive_hold_secs += extra_hold * 0.5
                    print(f"New hold time: {self.adaptive_hold_secs:.2f}s")
                elif actual_hold_time >= self.initial_hold_secs:
                    self.adaptive_hold_secs = actual_hold_time
                    print(f"Hold time was not met. Adjusting hold time down to: {self.adaptive_hold_secs:.2f}s")

                needs_reset = True
                self.rep_in_progress = False
                self.hold_start_time = None
                self.rep_counted_this_hold = False

        return {
            "newly_counted_rep": newly_counted_rep,
            "status_text": status_text,
            "needs_reset": needs_reset,
        }
