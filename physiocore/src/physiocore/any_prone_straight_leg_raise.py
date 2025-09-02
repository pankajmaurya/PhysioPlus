import json
import os
import time
from threading import Thread
import cv2
import mediapipe as mp

from physiocore.lib import modern_flags, graphics_utils, mp_utils
from physiocore.lib.graphics_utils import ExerciseInfoRenderer, ExerciseState, pause_loop
from physiocore.lib.basic_math import between, calculate_angle, calculate_mid_point
from physiocore.lib.file_utils import announceForCount, create_output_files, release_files
from physiocore.lib.landmark_utils import calculate_angle_between_landmarks, detect_feet_orientation, upper_body_is_lying_down
from physiocore.lib.mp_utils import pose2

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

class PoseTracker:
    def __init__(self, config, lenient_mode):
        self.l_rest_pose = False
        self.r_rest_pose = False
        self.l_raise_pose = False
        self.r_raise_pose = False

        self.knee_angle_min = config.get("knee_angle_min", 150)
        self.knee_angle_max = config.get("knee_angle_max", 180)
        self.rest_raise_min = config.get("rest_pose_raise_angle_min", 160)
        self.rest_raise_max = config.get("rest_pose_raise_angle_max", 180)
        self.raise_min = config.get("raise_pose_raise_angle_min", 100)
        self.raise_max = config.get("raise_pose_raise_angle_max", 140)
        self.lenient_mode = lenient_mode

    def update(self, prone_lying, l_knee, r_knee, l_ankle_close, r_ankle_close, l_raise, r_raise, lknee_high, rknee_high):
        if not self.l_rest_pose:
            lenient = self.lenient_mode or (r_ankle_close and between(self.knee_angle_min, r_knee, self.knee_angle_max))
            self.l_rest_pose = (lenient and prone_lying and l_ankle_close and
                               between(self.knee_angle_min, l_knee, self.knee_angle_max) and
                               between(self.rest_raise_min, l_raise, self.rest_raise_max))
            self.l_raise_pose = False

        if not self.r_rest_pose:
            lenient = self.lenient_mode or (l_ankle_close and between(self.knee_angle_min, l_knee, self.knee_angle_max))
            self.r_rest_pose = (lenient and prone_lying and r_ankle_close and
                               between(self.knee_angle_min, r_knee, self.knee_angle_max) and
                               between(self.rest_raise_min, r_raise, self.rest_raise_max))
            self.r_raise_pose = False

        if self.l_rest_pose:
            lenient = self.lenient_mode or (r_ankle_close and between(self.knee_angle_min, r_knee, self.knee_angle_max))
            self.l_raise_pose = (
                lenient and prone_lying and lknee_high and
                between(self.raise_min, l_raise, self.raise_max) and
                between(self.knee_angle_min, l_knee, self.knee_angle_max)
            )

        if self.r_rest_pose:
            lenient = self.lenient_mode or (l_ankle_close and between(self.knee_angle_min, l_knee, self.knee_angle_max))
            self.r_raise_pose = (
                lenient and prone_lying and rknee_high and
                between(self.raise_min, r_raise, self.raise_max) and
                between(self.knee_angle_min, r_knee, self.knee_angle_max)
            )

    def reset(self):
        self.l_rest_pose = False
        self.r_rest_pose = False
        self.l_raise_pose = False
        self.r_raise_pose = False

class AnyProneSLRTracker:
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
        self.l_check_timer = False
        self.r_check_timer = False
        self.l_time = None
        self.r_time = None
        self.cap = None
        self.output = None
        self.output_with_info = None
        self.renderer = ExerciseInfoRenderer()

    def _default_config_path(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(script_dir, "json", "any_prone_straight_leg_raise.json")

    def _load_config(self, path):
        try:
            with open(path) as conf:
                data = conf.read()
                return json.loads(data) if data else {}
        except FileNotFoundError:
            print("Config file not found, using default values")
            return {}

    def process_video(self, video_path, display=False):
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            print(f"Error opening video file: {video_path}")
            return 0

        input_fps = int(self.cap.get(cv2.CAP_PROP_FPS)) or 30
        delay = int(1000 / input_fps)
        if self.save_video:
            self.output, self.output_with_info = create_output_files(self.cap, self.save_video)

        while True:
            success, landmarks, frame, pose_landmarks = mp_utils.processFrameAndGetLandmarks(self.cap, pose2)
            if not success:
                break
            if frame is None:
                continue

            if self.save_video:
                self.output.write(frame)

            if not pose_landmarks:
                continue

            ground_level, lying_down = upper_body_is_lying_down(landmarks)
            feet_orien = detect_feet_orientation(landmarks)
            # Keypoints extraction
            lshoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
            rshoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
            shoulder_mid = calculate_mid_point((lshoulder.x, lshoulder.y), (rshoulder.x, rshoulder.y))
            lhip, rhip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value], landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value]
            lknee, rknee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value], landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value]
            lankle, rankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value], landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value]
            lshld, rshld = lshoulder, rshoulder
            lheel, rheel = landmarks[mp_pose.PoseLandmark.LEFT_HEEL.value], landmarks[mp_pose.PoseLandmark.RIGHT_HEEL.value]

            l_knee_angle = calculate_angle_between_landmarks(lhip, lknee, lankle)
            r_knee_angle = calculate_angle_between_landmarks(rhip, rknee, rankle)
            l_raise_angle = calculate_angle(shoulder_mid, (lhip.x, lhip.y), (lankle.x, lankle.y))
            r_raise_angle = calculate_angle(shoulder_mid, (rhip.x, rhip.y), (rankle.x, rankle.y))
            r_ankle_close = abs(ground_level - rankle.y) < 0.1
            l_ankle_close = abs(ground_level - lankle.y) < 0.1
            lknee_high = lheel.y < lshld.y
            rknee_high = rheel.y < rshld.y

            prone_lying = lying_down and (feet_orien == "Feet are downwards" or feet_orien == "either feet is downward")
            # print(f'feet are {feet_orien}')

            self.pose_tracker.update(prone_lying,
                                    l_knee_angle, r_knee_angle, l_ankle_close, r_ankle_close,
                                    l_raise_angle, r_raise_angle, lknee_high, rknee_high)

            # Timer and pose logic
            if self.pose_tracker.l_rest_pose and not self.pose_tracker.l_raise_pose:
                self.l_check_timer = False
            if self.pose_tracker.r_rest_pose and not self.pose_tracker.r_raise_pose:
                self.r_check_timer = False

            if prone_lying and self.pose_tracker.l_rest_pose and self.pose_tracker.l_raise_pose:
                self._handle_pose_hold(frame, leg='left')
            if prone_lying and self.pose_tracker.r_rest_pose and self.pose_tracker.r_raise_pose:
                self._handle_pose_hold(frame, leg='right')

            self._draw_info(
                frame, prone_lying, l_knee_angle, r_knee_angle, l_raise_angle, r_raise_angle,
                l_ankle_close, r_ankle_close, self.pose_tracker.l_rest_pose, self.pose_tracker.r_rest_pose,
                self.pose_tracker.l_raise_pose, self.pose_tracker.r_raise_pose, pose_landmarks, display=display
            )

            if self.save_video:
                self.output_with_info.write(frame)

            if display:
                if self.reps and self.count >= self.reps:
                    break
                key = cv2.waitKey(delay) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('p'):
                    should_quit = pause_loop()
                    if should_quit:
                        break

        self._cleanup()
        return self.count

    def start(self):
        self.process_video(self.video if self.video else 0, display=True)

    def _handle_pose_hold(self, frame, leg='left'):
        now = time.time()
        if leg == 'left':
            if not self.l_check_timer:
                self.l_time = now
                self.l_check_timer = True
                print("[AnyProne] time for raise for left leg ", self.l_time)
            else:
                if now - self.l_time > self.hold_secs:
                    self.count += 1
                    self.pose_tracker.reset()
                    self.l_check_timer = False
                    announceForCount(self.count)
                else:
                    cv2.putText(frame, f'hold left leg: {self.hold_secs - now + self.l_time:.2f}',
                                (250, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
        elif leg == 'right':
            if not self.r_check_timer:
                self.r_time = now
                self.r_check_timer = True
                print("[AnyProne] time for raise for right leg ", self.r_time)
            else:
                if now - self.r_time > self.hold_secs:
                    self.count += 1
                    self.pose_tracker.reset()
                    self.r_check_timer = False
                    announceForCount(self.count)
                else:
                    cv2.putText(frame, f'hold right leg: {self.hold_secs - now + self.r_time:.2f}',
                                (250, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

    def _draw_info(self, frame, prone_lying, l_knee_angle, r_knee_angle, l_raise_angle, r_raise_angle,
                   l_ankle_close, r_ankle_close,
                   l_resting, r_resting, l_raise, r_raise, pose_landmarks, display=True):
        """Draw exercise information using the shared renderer."""
        debug_info = None
        if self.debug:
            debug_info = {
                'Prone Lying Down': prone_lying,
                'Resting Pose': f'{l_resting}, {r_resting}',
                'Raise Pose': f'{l_raise}, {r_raise}',
                'Ankle floored': f'{l_ankle_close}, {r_ankle_close}',
                'Knee Angles': (l_knee_angle, r_knee_angle),
                'Raise angle': (l_raise_angle, r_raise_angle)
            }
        
        exercise_state = ExerciseState(
            count=self.count,
            debug=self.debug,
            render_all=self.render_all,
            exercise_name="Any Prone SLR",
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
    tracker = AnyProneSLRTracker()
    tracker.start()
