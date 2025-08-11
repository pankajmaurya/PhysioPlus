import cv2
import mediapipe as mp

# Initialize MediaPipe Pose
# Consider tweaking
default_pose = mp.solutions.pose.Pose(model_complexity=1,smooth_landmarks=True,min_detection_confidence=0.5, min_tracking_confidence=0.5)
pose2 = mp.solutions.pose.Pose(model_complexity=2,smooth_landmarks=True,min_detection_confidence=0.5, min_tracking_confidence=0.5)

def processFrameAndGetLandmarks(capture, pose=default_pose):
    if capture.isOpened():
        ret, frame = capture.read()
        if not ret:
            return False, None, None, None

        # Flip the frame for a mirror effect (optional)
        frame = cv2.flip(frame, 1)

        # Convert the BGR image to RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        frame.flags.writeable = False
        results = pose.process(frame)

        # Convert the image back to BGR for OpenCV rendering
        frame.flags.writeable = True
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        if not results.pose_landmarks:
            frame_height, frame_width, _ = frame.shape
            cv2.putText(frame, "Body not in frame", (frame_width // 2 - 100, frame_height // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            # Do not fail, but return None responses.
            return True, None, frame, None

        try:
            landmarks = results.pose_landmarks.landmark
            return True, landmarks, frame, results.pose_landmarks
        except:
            return False, None, None, None

    else:
        return False, None, None, None