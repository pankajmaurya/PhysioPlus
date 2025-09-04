import mediapipe as mp
from mediapipe.framework.formats import landmark_pb2

class LandmarkSmoother:
    def __init__(self, alpha=0.5):
        self.alpha = alpha
        self.smoothed_landmarks = None

    def __call__(self, landmarks):
        if landmarks is None:
            return None

        if self.smoothed_landmarks is None:
            # Deep copy
            self.smoothed_landmarks = landmark_pb2.NormalizedLandmarkList()
            self.smoothed_landmarks.landmark.extend(landmarks.landmark)
            return landmarks

        new_smoothed_landmarks_list = []
        for i in range(len(landmarks.landmark)):
            new_x = self.alpha * landmarks.landmark[i].x + (1 - self.alpha) * self.smoothed_landmarks.landmark[i].x
            new_y = self.alpha * landmarks.landmark[i].y + (1 - self.alpha) * self.smoothed_landmarks.landmark[i].y
            new_z = self.alpha * landmarks.landmark[i].z + (1 - self.alpha) * self.smoothed_landmarks.landmark[i].z

            new_landmark = landmark_pb2.NormalizedLandmark(x=new_x, y=new_y, z=new_z)
            new_smoothed_landmarks_list.append(new_landmark)

        # Create a new landmark list for returning
        return_landmarks = landmark_pb2.NormalizedLandmarkList()
        return_landmarks.landmark.extend(new_smoothed_landmarks_list)

        # Update the internal state
        self.smoothed_landmarks = landmark_pb2.NormalizedLandmarkList()
        self.smoothed_landmarks.landmark.extend(new_smoothed_landmarks_list)

        return return_landmarks