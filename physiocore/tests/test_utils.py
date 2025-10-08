def compute_hold_duration(base_duration, display_mode):
    """
    Computes the hold duration for a test.
    If display_mode is True, the duration is returned as is.
    Otherwise, the duration is set to 0.1 seconds to speed up tests.
    """
    if display_mode:
        return base_duration
    else:
        return 0.1