import collections
import json
import os
import time
from threading import Thread
import cv2
import mediapipe as mp

from physiocore.lib import modern_flags, mp_utils
from physiocore.lib.graphics_utils import ExerciseInfoRenderer, ExerciseState, pause_loop
from physiocore.lib.basic_math import between, calculate_distance
from physiocore.lib.file_utils import announceForCount, create_output_files, release_files
from physiocore.lib.landmark_utils import calculate_angle_between_landmarks, upper_body_is_lying_down

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

class LandmarkSmoother:
    """Class to smooth landmark positions over time to prevent flickering"""
    def __init__(self, buffer_size=5):
        self.buffer_size = buffer_size
        self.landmark_history = {}

    def update_landmarks(self, landmarks):
        if landmarks is None:
            return None

        smoothed_landmarks = []
        for i, landmark in enumerate(landmarks):
            if i not in self.landmark_history:
                self.landmark_history[i] = collections.deque(maxlen=self.buffer_size)

            self.landmark_history[i].append((landmark.x, landmark.y, landmark.z, landmark.visibility))

            if len(self.landmark_history[i]) > 1:
                avg_x = sum(item[0] for item in self.landmark_history[i]) / len(self.landmark_history[i])
                avg_y = sum(item[1] for item in self.landmark_history[i]) / len(self.landmark_history[i])
                avg_z = sum(item[2] for item in self.landmark_history[i]) / len(self.landmark_history[i])
                avg_v = sum(item[3] for item in self.landmark_history[i]) / len(self.landmark_history[i])

                smoothed_landmark = type('', (), {})()
                smoothed_landmark.x = avg_x
                smoothed_landmark.y = avg_y
                smoothed_landmark.z = avg_z
                smoothed_landmark.visibility = avg_v
            else:
                smoothed_landmark = landmark

            smoothed_landmarks.append(smoothed_landmark)

        return smoothed_landmarks

class PoseTracker:
    def __init__(self, config):
        self.l_extended_pose = False
        self.r_extended_pose = False
        self.l_flexed_pose = False
        self.r_flexed_pose = False
        self.l_leg_length = 0
        self.r_leg_length = 0
        self.l_cycle_completed = False
        self.r_cycle_completed = False

        self.l_extended_count = 0
        self.r_extended_count = 0
        self.l_flexed_count = 0
        self.r_flexed_count = 0

        self.required_consecutive_frames = 3
        self.l_in_transition = False
        self.r_in_transition = False
        self.l_last_cycle_time = time.time()
        self.r_last_cycle_time = time.time()
        self.min_cycle_time = 1.0

        self.knee_angle_extension_min = config.get('knee_angle_extension_min', 160)
        self.knee_angle_extension_max = config.get('knee_angle_extension_max', 180)
        self.knee_angle_flexion_min = config.get('knee_angle_flexion_min', 45)
        self.knee_angle_flexion_max = config.get('knee_angle_flexion_max', 90)
        self.heel_hip_min_distance_ratio = config.get('heel_hip_min_distance_ratio', 0.1)
        self.heel_hip_max_distance_ratio = config.get('heel_hip_max_distance_ratio', 0.5)

    def calculate_leg_length(self, hip, knee, ankle):
        try:
            hip_to_knee = calculate_distance((hip.x, hip.y), (knee.x, knee.y))
            knee_to_ankle = calculate_distance((knee.x, knee.y), (ankle.x, ankle.y))
            return hip_to_knee + knee_to_ankle
        except (AttributeError, TypeError):
            return 0

    def update(self, lying_down, l_knee_angle, r_knee_angle, l_heel_close, r_heel_close,
               l_hip_heel_dist, r_hip_heel_dist, lhip, lknee, lankle, rhip, rknee, rankle):

        self.l_leg_length = self.calculate_leg_length(lhip, lknee, lankle)
        self.r_leg_length = self.calculate_leg_length(rhip, rknee, rankle)

        l_heel_hip_ratio = l_hip_heel_dist / self.l_leg_length if self.l_leg_length > 0 else 0
        r_heel_hip_ratio = r_hip_heel_dist / self.r_leg_length if self.r_leg_length > 0 else 0

        # --- LEFT LEG TRACKING ---
        is_l_extended = (lying_down and l_heel_close and
                         between(self.knee_angle_extension_min, l_knee_angle, self.knee_angle_extension_max) and
                         l_heel_hip_ratio >= self.heel_hip_max_distance_ratio)

        if is_l_extended:
            self.l_extended_count += 1
        else:
            self.l_extended_count = 0

        if self.l_extended_count >= self.required_consecutive_frames:
            self.l_extended_pose = True

        if self.l_extended_pose and not self.l_in_transition:
            is_l_flexed = (lying_down and l_heel_close and
                           between(self.knee_angle_flexion_min, l_knee_angle, self.knee_angle_flexion_max) and
                           l_heel_hip_ratio <= self.heel_hip_min_distance_ratio)
            if is_l_flexed:
                self.l_flexed_count += 1
            else:
                self.l_flexed_count = 0
            if self.l_flexed_count >= self.required_consecutive_frames:
                self.l_flexed_pose = True
                self.l_in_transition = True

        if self.l_flexed_pose and self.l_in_transition:
            current_time = time.time()
            if is_l_extended and self.l_extended_count >= self.required_consecutive_frames and current_time - self.l_last_cycle_time >= self.min_cycle_time:
                self.l_cycle_completed = True
                self.l_last_cycle_time = current_time

        # --- RIGHT LEG TRACKING ---
        is_r_extended = (lying_down and r_heel_close and
                         between(self.knee_angle_extension_min, r_knee_angle, self.knee_angle_extension_max) and
                         r_heel_hip_ratio >= self.heel_hip_max_distance_ratio)

        if is_r_extended:
            self.r_extended_count += 1
        else:
            self.r_extended_count = 0

        if self.r_extended_count >= self.required_consecutive_frames:
            self.r_extended_pose = True

        if self.r_extended_pose and not self.r_in_transition:
            is_r_flexed = (lying_down and r_heel_close and
                           between(self.knee_angle_flexion_min, r_knee_angle, self.knee_angle_flexion_max) and
                           r_heel_hip_ratio <= self.heel_hip_min_distance_ratio)
            if is_r_flexed:
                self.r_flexed_count += 1
            else:
                self.r_flexed_count = 0
            if self.r_flexed_count >= self.required_consecutive_frames:
                self.r_flexed_pose = True
                self.r_in_transition = True

        if self.r_flexed_pose and self.r_in_transition:
            current_time = time.time()
            if is_r_extended and self.r_extended_count >= self.required_consecutive_frames and current_time - self.r_last_cycle_time >= self.min_cycle_time:
                self.r_cycle_completed = True
                self.r_last_cycle_time = current_time

    def resetLeftTracker(self):
        self.l_extended_pose = False
        self.l_flexed_pose = False
        self.l_cycle_completed = False
        self.l_extended_count = 0
        self.l_flexed_count = 0
        self.l_in_transition = False

    def resetRightTracker(self):
        self.r_extended_pose = False
        self.r_flexed_pose = False
        self.r_cycle_completed = False
        self.r_extended_count = 0
        self.r_flexed_count = 0
        self.r_in_transition = False


class HeelSlidesTracker:
    def __init__(self, config_path=None):
        flag_config_obj = modern_flags.parse_config()
        self.reps = flag_config_obj.reps
        self.debug = flag_config_obj.debug
        self.video = flag_config_obj.video
        self.render_all = flag_config_obj.render_all
        self.save_video = flag_config_obj.save_video
        self.lenient_mode = flag_config_obj.lenient_mode

        self.config = self._load_config(config_path or self._default_config_path())
        self.hold_secs = self.config.get("HOLD_SECS", 1)
        temporal_filter_size = self.config.get("TEMPORAL_FILTER_SIZE", 5)

        self.pose_tracker = PoseTracker(self.config)
        self.landmark_smoother = LandmarkSmoother(buffer_size=temporal_filter_size)
        self.count = 0
        self.cap = None
        self.output = None
        self.output_with_info = None
        self.renderer = ExerciseInfoRenderer()

    def _default_config_path(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(script_dir, "json", "heel_slides.json")

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
            if frame is None: continue
            if self.save_video: self.output.write(frame)

            smoothed_landmarks = self.landmark_smoother.update_landmarks(landmarks)
            if not smoothed_landmarks:
                if display:
                    self._draw_info(frame, None, None, None, None, None, None, None, None, None, None, None, pose_landmarks, display)
                    if cv2.waitKey(delay) & 0xFF == ord('q'): break
                continue

            ground_level, lying_down = upper_body_is_lying_down(smoothed_landmarks)

            try:
                lhip = smoothed_landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]
                rhip = smoothed_landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value]
                lknee = smoothed_landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value]
                rknee = smoothed_landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value]
                lankle = smoothed_landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value]
                rankle = smoothed_landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value]
                lheel = smoothed_landmarks[mp_pose.PoseLandmark.LEFT_HEEL.value]
                rheel = smoothed_landmarks[mp_pose.PoseLandmark.RIGHT_HEEL.value]
            except (IndexError, TypeError):
                continue

            l_knee_angle = calculate_angle_between_landmarks(lhip, lknee, lankle)
            r_knee_angle = calculate_angle_between_landmarks(rhip, rknee, rankle)
            l_hip_heel_dist = calculate_distance((lhip.x, lhip.y), (lheel.x, lheel.y))
            r_hip_heel_dist = calculate_distance((rhip.x, rhip.y), (rheel.x, rheel.y))
            r_heel_close = hasattr(rheel, 'y') and abs(ground_level - rheel.y) < 0.1
            l_heel_close = hasattr(lheel, 'y') and abs(ground_level - lheel.y) < 0.1

            self.pose_tracker.update(lying_down, l_knee_angle, r_knee_angle, l_heel_close, r_heel_close,
                                     l_hip_heel_dist, r_hip_heel_dist, lhip, lknee, lankle, rhip, rknee, rankle)

            if self.pose_tracker.l_cycle_completed:
                self.count += 1
                announceForCount(self.count)
                self.pose_tracker.resetLeftTracker()

            if self.pose_tracker.r_cycle_completed:
                self.count += 1
                announceForCount(self.count)
                self.pose_tracker.resetRightTracker()

            if display:
                if self.reps and self.count >= self.reps:
                    break
                self._draw_info(
                    frame, lying_down, l_knee_angle, r_knee_angle, l_heel_close, r_heel_close,
                    l_hip_heel_dist, r_hip_heel_dist,
                    self.pose_tracker.l_extended_pose, self.pose_tracker.r_extended_pose,
                    self.pose_tracker.l_flexed_pose, self.pose_tracker.r_flexed_pose,
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

    def _draw_info(self, frame, lying_down, l_knee_angle, r_knee_angle, l_heel_close, r_heel_close,
                   l_hip_heel_dist, r_hip_heel_dist, l_extended, r_extended, l_flexed, r_flexed,
                   pose_landmarks, display):
        """Draw exercise information using the shared renderer."""
        debug_info = None
        if self.debug and l_knee_angle is not None:
            l_heel_hip_ratio = l_hip_heel_dist / self.pose_tracker.l_leg_length if self.pose_tracker.l_leg_length > 0 else 0
            r_heel_hip_ratio = r_hip_heel_dist / self.pose_tracker.r_leg_length if self.pose_tracker.r_leg_length > 0 else 0
            debug_info = {
                'Lying Down': lying_down,
                'L Extended': l_extended,
                'R Extended': r_extended,
                'L Flexed': l_flexed,
                'R Flexed': r_flexed,
                'Heel Close': f'L: {l_heel_close}, R: {r_heel_close}',
                'Knee Angles': (l_knee_angle, r_knee_angle),
                'Heel-Hip Ratio': (l_heel_hip_ratio, r_heel_hip_ratio)
            }

        status_msgs = []
        if l_extended and not l_flexed:
            status_msgs.append("Left: Slide heel toward buttocks")
        elif l_flexed:
             status_msgs.append("Left: Return to starting position")

        if r_extended and not r_flexed:
            status_msgs.append("Right: Slide heel toward buttocks")
        elif r_flexed:
            status_msgs.append("Right: Return to starting position")

        exercise_state = ExerciseState(
            count=self.count,
            debug=self.debug,
            render_all=self.render_all,
            exercise_name="Heel Slides",
            debug_info=debug_info,
            status_messages=status_msgs,
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
    tracker = HeelSlidesTracker()
    tracker.start()
