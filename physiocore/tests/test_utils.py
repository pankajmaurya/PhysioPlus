"""Common utilities for PhysioCore tests."""
def compute_hold_duration(hold_with_display, display):
    """
    Compute the hold duration based on display setting.
    
    Args:
        hold_with_display (float): The hold duration when display is True
        display (bool): Whether display is enabled
        
    Returns:
        float: The computed hold duration
    """
    if display:
        return hold_with_display
    return hold_with_display / 1.8
