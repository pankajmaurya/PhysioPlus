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
from physiocore.lib.landmark_utils import calculate_angle_between_landmarks, upper_body_is_lying_down

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

class PoseTracker:
    def __init__(self, config, lenient_mode):
        self.resting_pose = False
        self.raise_pose = False
        self.knee_angle_min = config.get('knee_angle_min', 40)
        self.knee_angle_max = config.get('knee_angle_max', 90)
        self.rest_angle_min = config.get('rest_angle_min', 100)
        self.rest_angle_max = config.get('rest_angle_max', 130)
        self.raise_angle_min = config.get('raise_angle_min', 155)
        self.raise_angle_max = config.get('raise_angle_max', 180)
        self.lenient_mode = lenient_mode

    def update(self, lying_down, l_knee, r_knee, l_ankle, r_ankle, l_raise, r_raise):
        if not self.resting_pose:
            lenient = (
                self.lenient_mode or (
                    l_ankle and r_ankle and
                    between(self.knee_angle_min, r_knee, self.knee_angle_max) and
                    between(self.knee_angle_min, l_knee, self.knee_angle_max) and
                    between(self.rest_angle_min, l_raise, self.rest_angle_max) and
                    between(self.rest_angle_min, r_raise, self.rest_angle_max)
                )
            )
            self.resting_pose = (
                lenient and lying_down and (l_ankle or r_ankle) and
                (between(self.knee_angle_min, r_knee, self.knee_angle_max) or
                 between(self.knee_angle_min, l_knee, self.knee_angle_max)) and
                (between(self.rest_angle_min, l_raise, self.rest_angle_max) or
                 between(self.rest_angle_min, r_raise, self.rest_angle_max))
            )
            self.raise_pose = False

        if self.resting_pose:
            lenient = (
                self.lenient_mode or (
                    between(self.raise_angle_min, l_raise, self.raise_angle_max) and
                    between(self.raise_angle_min, r_raise, self.raise_angle_max) and
                    between(self.knee_angle_min, r_knee, self.knee_angle_max) and
                    between(self.knee_angle_min, l_knee, self.knee_angle_max)
                )
            )
            self.raise_pose = (
                (lenient and
                 (between(self.raise_angle_min, l_raise, self.raise_angle_max) or
                  between(self.raise_angle_min, r_raise, self.raise_angle_max)) and
                 (between(self.knee_angle_min, r_knee, self.knee_angle_max) or
                  between(self.knee_angle_min, l_knee, self.knee_angle_max)))
            )

    def reset(self):
        self.resting_pose = False
        self.raise_pose = False

class BridgingTracker:
    def __init__(self, config_path=None):
        flag_config_obj = modern_flags.parse_config()
        self.reps = flag_config_obj.reps
        self.debug = flag_config_obj.debug
        self.video = flag_config_obj.video
        self.render_all = flag_config_obj.render_all
        self.save_video = flag_config_obj.save_video
        self.lenient_mode = flag_config_obj.lenient_mode

        self.config = self._load_config(config_path or self._default_config_path())
        self.hold_secs = self.config.get("HOLD_SECS", 5)

        self.pose_tracker = PoseTracker(self.config, self.lenient_mode)
        self.count = 0
        self.check_timer = False
        self.old_time = None
        self.cap = None
        self.output = None
        self.output_with_info = None
        self.renderer = ExerciseInfoRenderer()

    def _default_config_path(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(script_dir, "json", "bridging.json")

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

            ground_level, lying_down = upper_body_is_lying_down(landmarks)
            lshoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
            rshoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
            lhip, rhip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value], landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value]
            lknee, rknee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value], landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value]
            lankle, rankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value], landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value]
            l_knee_angle = calculate_angle_between_landmarks(lhip, lknee, lankle)
            r_knee_angle = calculate_angle_between_landmarks(rhip, rknee, rankle)
            l_raise_angle = calculate_angle((lshoulder.x, lshoulder.y), (lhip.x, lhip.y), (lknee.x, lknee.y))
            r_raise_angle = calculate_angle((rshoulder.x, rshoulder.y), (rhip.x, rhip.y), (rknee.x, rknee.y))
            l_ankle_close = abs(ground_level - lankle.y) < 0.1
            r_ankle_close = abs(ground_level - rankle.y) < 0.1

            self.pose_tracker.update(
                lying_down, l_knee_angle, r_knee_angle, l_ankle_close, r_ankle_close,
                l_raise_angle, r_raise_angle
            )

            if self.pose_tracker.resting_pose and not self.pose_tracker.raise_pose:
                self.check_timer = False

            if self.pose_tracker.resting_pose and self.pose_tracker.raise_pose:
                self._handle_pose_hold(frame if display else None)

            if display:
                if self.reps and self.count >= self.reps:
                    break
                self._draw_info(
                    frame, lying_down, l_knee_angle, r_knee_angle, l_raise_angle, r_raise_angle,
                    l_ankle_close, r_ankle_close, self.pose_tracker.resting_pose, self.pose_tracker.raise_pose, 
                    pose_landmarks, display
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

    def _handle_pose_hold(self, frame=None):
        if not self.check_timer:
            self.old_time = time.time()
            self.check_timer = True
            print("[Bridging] time for raise", self.old_time)
        else:
            cur_time = time.time()
            if cur_time - self.old_time > self.hold_secs:
                self.count += 1
                self.pose_tracker.reset()
                self.check_timer = False
                announceForCount(self.count)
            elif frame is not None:
                cv2.putText(
                    frame,
                    f'hold pose: {self.hold_secs - cur_time + self.old_time:.2f}',
                    (250, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2
                )

    def _draw_info(self, frame, lying_down, l_knee_angle, r_knee_angle, l_raise_angle, r_raise_angle,
                   l_ankle_close, r_ankle_close, resting_pose, raise_pose, pose_landmarks, display):
        """Draw exercise information using the shared renderer."""
        debug_info = None
        if self.debug:
            debug_info = {
                'Lying Down': lying_down,
                'Resting Pose': resting_pose,
                'Raise Pose': raise_pose,
                'Ankle floored': f'{l_ankle_close}, {r_ankle_close}',
                'Knee Angles': (l_knee_angle, r_knee_angle),
                'Raise angle': (l_raise_angle, r_raise_angle)
            }
        
        exercise_state = ExerciseState(
            count=self.count,
            debug=self.debug,
            render_all=self.render_all,
            exercise_name="Bridging",
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
    tracker = BridgingTracker()
    tracker.start()
