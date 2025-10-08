import cv2
import mediapipe as mp

from physiocore.lib import modern_flags, mp_utils
from physiocore.lib.graphics_utils import ExerciseInfoRenderer, ExerciseState, pause_loop
from physiocore.lib.basic_math import between
from physiocore.lib.file_utils import announceForCount, create_output_files, release_files
from physiocore.lib.timer_utils import AdaptiveHoldTimer

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

class PoseTracker:
    def __init__(self):
        self.squeezed = False
        self.expand = False

    def updateTracker(self, left_elbow, left_shoulder, right_elbow, right_shoulder):
        left_elbow_pass = self.is_elbow_squeezed(left_elbow, left_shoulder)
        right_elbow_pass = self.is_elbow_squeezed(right_elbow, right_shoulder)

        left_elbow_rest = self.is_elbow_expanded(left_elbow, left_shoulder)
        right_elbow_rest = self.is_elbow_expanded(right_elbow, right_shoulder)

        if left_elbow_rest and right_elbow_rest:
            self.expand = True

        if left_elbow_pass and right_elbow_pass and self.expand:
            self.squeezed = True  # Mark as squeezed       
        #elif not (left_elbow_pass and right_elbow_pass):
        #    self.squeezed = False  # Reset squeeze state

    def resetTracker(self):
        self.squeezed = False
        self.expand = False

    # Function to check if elbow passes backward relative to the body
    def is_elbow_squeezed(self, elbow, shoulder):
        return shoulder[0] < elbow[0]  # Compare x-coordinates (relative to the camera frame)
    
    def is_elbow_expanded(self, elbow, shoulder):
        return shoulder[0] > elbow[0]  # Compare x-coordinates (relative to the camera frame)

class ShoulderBladeSqueezeTracker2:
    def __init__(self, test_mode=False, config_path=None):
        flag_config_obj = modern_flags.parse_config()
        self.reps = flag_config_obj.reps
        self.debug = flag_config_obj.debug
        self.video = flag_config_obj.video
        self.render_all = flag_config_obj.render_all
        self.save_video = flag_config_obj.save_video
        self.lenient_mode = flag_config_obj.lenient_mode

        self.pose_tracker = PoseTracker()
        self.count = 0
        self.cap = None
        self.output = None
        self.output_with_info = None
        self.renderer = ExerciseInfoRenderer()

    def start(self):
        return self.process_video(display=True)

    def process_video(self, video_path=None, display=True):
        self.video = video_path if video_path is not None else self.video
        self.cap = cv2.VideoCapture(self.video if self.video else 0)

        if not self.cap.isOpened():
            print(f"Error opening video stream or file: {self.video}")
            return 0

        input_fps = int(self.cap.get(cv2.CAP_PROP_FPS)) or 30
        delay = int(1000 / input_fps)
        if self.save_video:
            self.output, self.output_with_info = create_output_files(self.cap, self.save_video)

        while True:
            success, landmarks, frame, pose_landmarks = mp_utils.processFrameAndGetLandmarks(self.cap)
            if not success:
                break
            
            if frame is None:
                continue
            
            if self.save_video:
                self.output.write(frame)

            if not pose_landmarks:
                continue

            LEFT_WRIST = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x, 
                          landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
            RIGHT_WRIST = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].x, 
                           landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y]
            left_elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x, 
                          landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
            right_elbow = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x, 
                           landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]
            left_shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, 
                             landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
            right_shoulder = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x, 
                              landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]

            # Check if both elbows pass behind their respective shoulders
            self.pose_tracker.updateTracker(left_elbow, left_shoulder, right_elbow, right_shoulder)

            if self.pose_tracker.squeezed:
                self.count += 1
                self.pose_tracker.resetTracker()

            if display:
                self._draw_info(frame, pose_landmarks, display)

            if self.save_video and self.debug:
                self.output_with_info.write(frame)

            if display:
                if self.reps and self.count >= self.reps:
                    break
                key = cv2.waitKey(delay) & 0xFF
                if key == ord("q"):
                    break
                elif key == ord("p"):
                    should_quit = pause_loop()
                    if should_quit:
                        break

        self._cleanup()
        return self.count

    def _draw_info(self, frame, pose_landmarks, display):
        debug_info = None
        if self.debug:
            debug_info = {
                'Squeezed': self.pose_tracker.squeezed,
                'Expand': self.pose_tracker.expand,
            }

        exercise_state = ExerciseState(
            count=self.count,
            debug=self.debug,
            render_all=self.render_all,
            exercise_name="Shoulder Blade Squeeze",
            debug_info=debug_info,
            pose_landmarks=pose_landmarks,
            display=display
        )

        self.renderer.render_complete_frame(frame, exercise_state)

    def _cleanup(self):
        if self.cap:
            self.cap.release()
        if self.save_video:
            release_files(self.output, self.output_with_info)
        cv2.destroyAllWindows()
        print(f"Final count: {self.count}")

if __name__ == "__main__":
    tracker = ShoulderBladeSqueezeTracker2()
    tracker.start()
