import mediapipe as mp
from mediapipe.framework.formats import landmark_pb2
from typing import Optional

class LandmarkSmoother:
    """
    Exponential moving average smoother for MediaPipe landmarks.
    """
    def __init__(self, alpha: float = 0.5):
        """
        Initializes the LandmarkSmoother.

        Args:
            alpha: The smoothing factor. A higher value gives more weight to the
                   current input, while a lower value gives more weight to the
                   past smoothed landmarks.
        """
        self.alpha = alpha
        self.smoothed_landmarks: Optional[landmark_pb2.NormalizedLandmarkList] = None

    def __call__(self, landmarks: Optional[landmark_pb2.NormalizedLandmarkList]) -> Optional[landmark_pb2.NormalizedLandmarkList]:
        """
        Applies exponential smoothing to the landmarks.

        Args:
            landmarks: A NormalizedLandmarkList from MediaPipe.

        Returns:
            A new NormalizedLandmarkList with smoothed landmarks, or None if the
            input was None.
        """
        if landmarks is None:
            return None

        if self.smoothed_landmarks is None:
            # On the first frame, just store the landmarks and return them.
            self.smoothed_landmarks = landmark_pb2.NormalizedLandmarkList()
            self.smoothed_landmarks.CopyFrom(landmarks)
            return landmarks

        # Create a new list to store the smoothed landmarks.
        new_smoothed_landmarks = landmark_pb2.NormalizedLandmarkList()

        for i in range(len(landmarks.landmark)):
            # Get current and previous landmarks.
            current_lm = landmarks.landmark[i]
            prev_smooth_lm = self.smoothed_landmarks.landmark[i]

            # Apply EMA.
            new_x = self.alpha * current_lm.x + (1 - self.alpha) * prev_smooth_lm.x
            new_y = self.alpha * current_lm.y + (1 - self.alpha) * prev_smooth_lm.y
            new_z = self.alpha * current_lm.z + (1 - self.alpha) * prev_smooth_lm.z

            # Create the new landmark, copying visibility and presence.
            new_lm = new_smoothed_landmarks.landmark.add()
            new_lm.x = new_x
            new_lm.y = new_y
            new_lm.z = new_z
            if current_lm.HasField('visibility'):
                new_lm.visibility = current_lm.visibility
            if current_lm.HasField('presence'):
                new_lm.presence = current_lm.presence

        # Update the internal state and return the new smoothed landmarks.
        self.smoothed_landmarks = new_smoothed_landmarks
        return new_smoothed_landmarks

    def reset(self):
        """
        Resets the internal state of the smoother.
        """
        self.smoothed_landmarks = None