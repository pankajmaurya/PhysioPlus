import json
import os
import time
from threading import Thread
import cv2
import mediapipe as mp

from physiocore.lib import modern_flags, graphics_utils, mp_utils
from physiocore.lib.graphics_utils import ExerciseInfoRenderer, ExerciseState, pause_loop
from physiocore.lib.basic_math import between, calculate_angle
from physiocore.lib.file_utils import announceForCount, create_output_files, release_files
from physiocore.lib.landmark_utils import calculate_angle_between_landmarks

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

class PoseTracker:
    def __init__(self, config, lenient_mode):
        self.threshold = config.get('threshold', 0.05)
        self.state = "center"
        self.lenient_mode = lenient_mode

    def update(self, nose, left_shoulder, right_shoulder):
        shoulder_center_x = (left_shoulder.x + right_shoulder.x) / 2

        if nose.x > shoulder_center_x + self.threshold:
            self.state = "right"
        elif nose.x < shoulder_center_x - self.threshold:
            self.state = "left"
        else:
            self.state = "center"

    def reset(self):
        self.state = "center"

class NeckRotationTracker:
    def __init__(self, config_path=None):
        flag_config_obj = modern_flags.parse_config()
        self.reps = flag_config_obj.reps
        self.debug = flag_config_obj.debug
        self.video = flag_config_obj.video
        self.render_all = flag_config_obj.render_all
        self.save_video = flag_config_obj.save_video
        self.lenient_mode = flag_config_obj.lenient_mode

        self.config = self._load_config(config_path or self._default_config_path())

        self.pose_tracker = PoseTracker(self.config, self.lenient_mode)
        self.count = 0
        self.stage = "left" # Start by looking for a left rotation
        self.cap = None
        self.output = None
        self.output_with_info = None
        self.renderer = ExerciseInfoRenderer()

    def _default_config_path(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(script_dir, "json", "neck_rotation.json")

    def _load_config(self, path):
        try:
            with open(path) as conf:
                data = conf.read()
                return json.loads(data) if data else {}
        except FileNotFoundError:
            print("Config file not found, using default values")
            return {}

    def start(self):
        self.process_video()

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

            nose = landmarks[mp_pose.PoseLandmark.NOSE.value]
            left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
            right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]

            self.pose_tracker.update(nose, left_shoulder, right_shoulder)

            if self.stage == "left" and self.pose_tracker.state == "left":
                self.stage = "right"
            elif self.stage == "right" and self.pose_tracker.state == "right":
                self.count += 1
                self.stage = "left"
                announceForCount(self.count)


            if display:
                if self.reps and self.count >= self.reps:
                    break
                self._draw_info(
                    frame, self.pose_tracker.state, pose_landmarks, display
                )

                if self.save_video and self.debug:
                    self.output_with_info.write(frame)

                key = cv2.waitKey(delay) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('p'):
                    should_quit = pause_loop()
                    if should_quit:
                        break

        self._cleanup(display=display)
        return self.count

    def _draw_info(self, frame, state, pose_landmarks, display):
        """Draw exercise information using the shared renderer."""
        debug_info = None
        if self.debug:
            debug_info = {
                'State': state
            }

        exercise_state = ExerciseState(
            count=self.count,
            debug=self.debug,
            render_all=self.render_all,
            exercise_name="Neck Rotation",
            debug_info=debug_info,
            pose_landmarks=pose_landmarks,
            display=display
        )

        self.renderer.render_complete_frame(frame, exercise_state)

    def _cleanup(self, display=True):
        if self.cap:
            self.cap.release()
        if self.save_video:
            release_files(self.output, self.output_with_info)
        if display:
            cv2.destroyAllWindows()
        print(f"Final count: {self.count}")

if __name__ == "__main__":
    tracker = NeckRotationTracker()
    tracker.start()
