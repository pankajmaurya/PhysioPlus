from physiocore.ankle_toe_movement import AnkleToeMovementTracker
from physiocore.cobra_stretch import CobraStretchTracker
from physiocore.bridging import BridgingTracker
from physiocore.any_straight_leg_raise import AnySLRTracker
from physiocore.any_prone_straight_leg_raise import AnyProneSLRTracker

_TRACKERS = {
    "ankle_toe_movement": AnkleToeMovementTracker,
    "cobra_stretch": CobraStretchTracker,
    "bridging": BridgingTracker,
    "any_slr": AnySLRTracker,
    "any_prone_slr": AnyProneSLRTracker,
}


def create_tracker(exercise_name, config_path=None, reps=None):
    """
    Factory function to create an exercise tracker.

    Args:
        exercise_name (str): The name of the exercise to track.
        config_path (str, optional): Path to a custom configuration file. Defaults to None.
        reps (int, optional): Number of reps to perform, None for continuous.

    Returns:
        An instance of the specified exercise tracker.

    Raises:
        ValueError: If the exercise_name is not supported.
    """
    tracker_class = _TRACKERS.get(exercise_name)
    if tracker_class:
        return tracker_class(config_path, reps=reps)
    else:
        raise ValueError(f"Unknown exercise: {exercise_name}")
