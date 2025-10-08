import json
import os
import cv2
import mediapipe as mp

from physiocore.lib import modern_flags, mp_utils
from physiocore.lib.graphics_utils import ExerciseInfoRenderer, ExerciseState, pause_loop
from physiocore.lib.basic_math import calculate_distance
from physiocore.lib.file_utils import announceForCount, create_output_files, release_files
from physiocore.lib.timer_utils import AdaptiveHoldTimer
from physiocore.lib.landmark_utils import upper_body_is_lying_down

mp_pose = mp.solutions.pose

class PoseTracker:
    def __init__(self, config, lenient_mode):
        self.resting_pose = False
        self.squeeze_pose = False
        # Ratio of shoulder distance to hip distance.
        # Higher value means shoulders are wider (relaxed).
        # Lower value means shoulders are narrower (squeezed).
        self.rest_threshold = config.get("rest_threshold", 1.1)
        self.squeeze_threshold = config.get("squeeze_threshold", 0.9)
        self.lenient_mode = lenient_mode # Not used for now, but keep for consistency

    def update(self, shoulder_hip_ratio):
        is_resting = shoulder_hip_ratio > self.rest_threshold
        is_squeezing = shoulder_hip_ratio < self.squeeze_threshold

        if not self.resting_pose:
            # User must first be in a resting position to start a repetition.
            if is_resting:
                self.resting_pose = True
            self.squeeze_pose = False
        else:
            # If a repetition is in progress, check for the squeeze.
            self.squeeze_pose = is_squeezing

    def reset(self):
        self.resting_pose = False
        self.squeeze_pose = False

class ShoulderBladeSqueezeTracker:
    def __init__(self, test_mode=False, config_path=None):
        flag_config_obj = modern_flags.parse_config()
        self.reps = flag_config_obj.reps
        self.debug = flag_config_obj.debug
        self.video = flag_config_obj.video
        self.render_all = flag_config_obj.render_all
        self.save_video = flag_config_obj.save_video
        self.lenient_mode = flag_config_obj.lenient_mode

        self.config = self._load_config(config_path or self._default_config_path())
        self.hold_secs = self.config.get("HOLD_SECS", 3)

        self.pose_tracker = PoseTracker(self.config, self.lenient_mode)
        self.timer = AdaptiveHoldTimer(initial_hold_secs=self.hold_secs, test_mode=test_mode)
        self.count = 0
        self.cap = None
        self.output = None
        self.output_with_info = None
        self.renderer = ExerciseInfoRenderer()

    def _default_config_path(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(script_dir, "json", "shoulder_blade_squeeze.json")

    def _load_config(self, path):
        try:
            with open(path) as conf:
                data = conf.read()
                return json.loads(data) if data else {}
        except FileNotFoundError:
            print("Config file not found, using default values")
            return {}

    def start(self):
        return self.process_video(display=True)

    def process_video(self, video_path=None, display=True):
        self.video = video_path if video_path is not None else self.video
        self.cap = cv2.VideoCapture(self.video if self.video else 0)

        if not self.cap.isOpened():
            print(f"Error opening video stream or file: {self.video}")
            return 0

        input_fps = int(self.cap.get(cv2.CAP_PROP_FPS)) or 30
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
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

            _ , lying_down = upper_body_is_lying_down(landmarks)

            lhip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]
            rhip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value]
            lshoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
            rshoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]

            shoulder_hip_ratio = 0
            landmarks_visible = (lhip.visibility > 0.5 and rhip.visibility > 0.5 and lshoulder.visibility > 0.5 and rshoulder.visibility > 0.5)

            if landmarks_visible:
                shoulder_dist = calculate_distance(lshoulder, rshoulder, height, width)
                hip_dist = calculate_distance(lhip, rhip, height, width)
                shoulder_hip_ratio = shoulder_dist / hip_dist if hip_dist > 0 else 0

            if not lying_down and landmarks_visible:
                self.pose_tracker.update(shoulder_hip_ratio)
            else:
                self.pose_tracker.reset()

            timer_status = self.timer.update(in_hold_pose=self.pose_tracker.squeeze_pose)
            if timer_status["newly_counted_rep"]:
                self.count += 1
                announceForCount(self.count)

            if timer_status["needs_reset"]:
                self.pose_tracker.reset()

            if display:
                if timer_status["status_text"]:
                    cv2.putText(
                        frame,
                        timer_status["status_text"],
                        (250, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2
                    )

                self._draw_info(
                    frame, shoulder_hip_ratio, lying_down, pose_landmarks, display
                )

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

    def set_hold_secs(self, hold_secs):
        self.hold_secs = hold_secs
        if hasattr(self, 'timer'):
            self.timer.set_hold_time(hold_secs)

    def _draw_info(self, frame, shoulder_hip_ratio, lying_down, pose_landmarks, display):
        debug_info = None
        if self.debug:
            debug_info = {
                'Lying Down': lying_down,
                'Resting Pose': self.pose_tracker.resting_pose,
                'Squeeze Pose': self.pose_tracker.squeeze_pose,
                'Shoulder-Hip Ratio': round(shoulder_hip_ratio, 2),
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
    tracker = ShoulderBladeSqueezeTracker()
    tracker.start()