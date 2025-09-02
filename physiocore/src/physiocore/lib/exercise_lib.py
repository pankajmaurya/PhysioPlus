from enum import Enum

class ExerciseType(Enum):
    """Supported exercise types"""
    ANKLE_TOE = "ankle_toe_movement"
    BRIDGING = "bridging"
    COBRA = "cobra_stretch"
    PRONE_SLR = "any_prone_slr"
    SLR = "any_slr"
