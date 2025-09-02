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
from physiocore.lib.landmark_utils import calculate_angle_between_landmarks, lower_body_on_ground, detect_feet_orientation

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

class PoseTracker:
    def __init__(self, config, lenient_mode):
        self.resting_pose = False
        self.raise_pose = False
        self.elbow_rest_min = config.get("elbow_rest_min", 0)
        self.elbow_rest_max = config.get("elbow_rest_max", 70)
        self.elbow_raise_min = config.get("elbow_raise_min", 110)
        self.elbow_raise_max = config.get("elbow_raise_max", 180)
        self.raise_angle_min = config.get("raise_angle_min", 150)
        self.raise_angle_max = config.get("raise_angle_max", 180)
        self.lenient_mode = lenient_mode

    def update(self, a_l_elbow, a_r_elbow, raise_angle, wrist_close, wrist_near_torse, head_angle, lower_body_prone):
        if not self.resting_pose:
            lenient = self.lenient_mode or (wrist_close and wrist_near_torse and head_angle < 100)
            self.resting_pose = (
                lenient and lower_body_prone and
                ((self.elbow_rest_min < a_l_elbow < self.elbow_rest_max) or
                 (self.elbow_rest_min < a_r_elbow < self.elbow_rest_max)) and
                self.raise_angle_max > raise_angle > self.raise_angle_min
            )
            self.raise_pose = False
        if self.resting_pose:
            lenient = self.lenient_mode or (wrist_close and head_angle > 125)
            self.raise_pose = (
                lenient and lower_body_prone and
                ((self.elbow_raise_min < a_l_elbow < self.elbow_raise_max) or
                 (self.elbow_raise_min < a_r_elbow < self.elbow_raise_max)) and
                raise_angle < self.raise_angle_min
            )

    def reset(self):
        self.resting_pose = False
        self.raise_pose = False

class CobraStretchTracker:
    def __init__(self, config_path=None):
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
        self.count = 0
        self.check_timer = False
        self.start_time = None
        self.cap = None
        self.output = None
        self.output_with_info = None
        self.renderer = ExerciseInfoRenderer()

    def _default_config_path(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(script_dir, "json", "cobra_stretch.json")

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
            ground_level, on_ground = lower_body_on_ground(landmarks)
            # Landmark extraction as per your original logic
            lhip, rhip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value], landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value]
            lshoulder, rshoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value], landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
            lwrist, rwrist = landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value], landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value]
            lelbow, relbow = landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value], landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value]
            lknee, rknee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value], landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value]
            nose = landmarks[mp_pose.PoseLandmark.NOSE.value]
            angle_left_elb = calculate_angle_between_landmarks(lshoulder, lelbow, lwrist)
            angle_right_elb = calculate_angle_between_landmarks(rshoulder, relbow, rwrist)
            shoulder_mid = calculate_mid_point((lshoulder.x, lshoulder.y), (rshoulder.x, rshoulder.y))
            hip_mid = calculate_mid_point((lhip.x, lhip.y), (rhip.x, rhip.y))
            wrist_mid = calculate_mid_point((lwrist.x, lwrist.y), (rwrist.x, rwrist.y))
            nose_coords = (nose.x, nose.y)
            knee = lknee if (lknee.visibility > rknee.visibility) else rknee
            raise_angle = calculate_angle(shoulder_mid, hip_mid, (knee.x, knee.y))
            head_angle = calculate_angle(nose_coords, shoulder_mid, wrist_mid)
            r_wrist_close = abs(ground_level - rwrist.y) < 0.1
            l_wrist_close = abs(ground_level - lwrist.y) < 0.1
            r_wrist_near_torse = between(lshoulder.x, lwrist.x, lhip.x)
            l_wrist_near_torse = between(rshoulder.x, rwrist.x, rhip.x)
            feet_orien = detect_feet_orientation(landmarks)
            lower_body_prone = on_ground and (feet_orien == "Feet are downwards" or feet_orien == "either feet is downward")
            # Update tracker
            self.pose_tracker.update(
                angle_left_elb, angle_right_elb, raise_angle,
                l_wrist_close and r_wrist_close,
                l_wrist_near_torse and r_wrist_near_torse,
                head_angle, lower_body_prone
            )
            # Timer logic
            if self.pose_tracker.resting_pose and not self.pose_tracker.raise_pose:
                self.check_timer = False
            if self.pose_tracker.resting_pose and self.pose_tracker.raise_pose:
                self._handle_pose_hold(frame)
            # Draw info and pose
            if display:
                self._draw_info(
                    frame, angle_left_elb, angle_right_elb, raise_angle, head_angle,
                    l_wrist_close, r_wrist_close, l_wrist_near_torse, r_wrist_near_torse,
                    lower_body_prone, feet_orien, pose_landmarks, display
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

    def _handle_pose_hold(self, frame):
        if not self.check_timer:
            self.start_time = time.time()
            self.check_timer = True
            print("[Cobra] time for raise", self.start_time)
        else:
            cur_time = time.time()
            if cur_time - self.start_time > self.hold_secs:
                self.count += 1
                self.pose_tracker.reset()
                self.check_timer = False
                announceForCount(self.count)
 
            else:
                cv2.putText(
                    frame,
                    f"hold pose: {self.hold_secs - cur_time + self.start_time:.2f}",
                    (250, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2
                )

    def _draw_info(self, frame, angle_left_elb, angle_right_elb, raise_angle, head_angle,
                   l_wrist_close, r_wrist_close, l_wrist_near_torse, r_wrist_near_torse,
                   lower_body_prone, feet_orien, pose_landmarks, display):
        """Draw exercise information using the shared renderer."""
        debug_info = None
        if self.debug:
            debug_info = {
                'Resting Pose': self.pose_tracker.resting_pose,
                'Raise Pose': self.pose_tracker.raise_pose,
                'lowerbody grounded': lower_body_prone,
                'elbow angle(L,R)': (angle_left_elb, angle_right_elb),
                'wrist close': l_wrist_close and r_wrist_close,
                'wrist near torse': l_wrist_near_torse and r_wrist_near_torse,
                'head angle': head_angle,
                'raise angle': raise_angle,
                'feet orientation': feet_orien
            }
        
        exercise_state = ExerciseState(
            count=self.count,
            debug=self.debug,
            render_all=self.render_all,
            exercise_name="Cobra Stretch",
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
    tracker = CobraStretchTracker()
    tracker.start()
