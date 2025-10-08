"""
This module contains utility functions for tests.
"""

def compute_hold_duration(hold_with_display, display, no_display_value=None, factor=1.0):
    """
    Computes the hold duration based on whether the display is on or off.
    """
    if display:
        return hold_with_display
    if no_display_value is not None:
        return no_display_value
    return hold_with_display / factor