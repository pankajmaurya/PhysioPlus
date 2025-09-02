import json
import os
import time
from threading import Thread
import cv2
import mediapipe as mp

from physiocore.lib import modern_flags, graphics_utils, mp_utils
from physiocore.lib.graphics_utils import ExerciseInfoRenderer, ExerciseState, pause_loop
from physiocore.lib.basic_math import between
from physiocore.lib.file_utils import announceForCount, create_output_files, release_files
from physiocore.lib.landmark_utils import calculate_angle_between_landmarks, lower_body_on_ground
from physiocore.lib.mp_utils import pose2

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose


class PoseTracker:
    def __init__(self, relax_min, relax_max, stretch_min, stretch_max, lenient_mode):
        self.relax_pose = False
        self.stretch_pose = False
        self.relax_min = relax_min
        self.relax_max = relax_max
        self.stretch_min = stretch_min
        self.stretch_max = stretch_max
        self.lenient_mode = lenient_mode

    def update(self, lower_body_grounded, l_angle, r_angle):
        if not self.relax_pose:
            self.relax_pose = (
                lower_body_grounded
                and between(self.relax_min, l_angle, self.relax_max)
                and between(self.relax_min, r_angle, self.relax_max)
            )
            self.stretch_pose = False

        if self.relax_pose:
            l_stretched = between(self.stretch_min, l_angle, self.stretch_max)
            r_stretched = between(self.stretch_min, r_angle, self.stretch_max)
            ankles_stretched = (l_stretched or r_stretched) if self.lenient_mode else (l_stretched and r_stretched)
            self.stretch_pose = lower_body_grounded and ankles_stretched

    def reset(self):
        self.relax_pose = False
        self.stretch_pose = False


class AnkleToeMovementTracker:
    def __init__(self, config_path=None):
        flag_config_obj = modern_flags.parse_config()
        self.reps = flag_config_obj.reps
        self.debug = flag_config_obj.debug
        self.video = flag_config_obj.video
        self.render_all = flag_config_obj.render_all
        self.save_video = flag_config_obj.save_video
        self.lenient_mode = flag_config_obj.lenient_mode

        self.config = self._load_config(config_path or self._default_config_path())

        self.relax_min = self.config.get("relax_ankle_angle_min", 80)
        self.relax_max = self.config.get("relax_ankle_angle_max", 110)
        self.stretch_min = self.config.get("stretch_ankle_angle_min", 140)
        self.stretch_max = self.config.get("stretch_ankle_angle_max", 180)
        self.hold_secs = self.config.get("HOLD_SECS", 2)

        self.pose_tracker = PoseTracker(
            self.relax_min, self.relax_max, self.stretch_min, self.stretch_max, self.lenient_mode
        )
        self.count = 0
        self.check_timer = False
        self.old_time = None
        self.cap = None
        self.output = None
        self.output_with_info = None
        self.renderer = ExerciseInfoRenderer()

    def _default_config_path(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(script_dir, "json", "ankle_toe_movement.json")

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
            success, landmarks, frame, pose_landmarks = mp_utils.processFrameAndGetLandmarks(self.cap, pose2)
            if not success:
                break
            if frame is None:
                continue

            if self.save_video:
                self.output.write(frame)

            if not pose_landmarks:
                continue

            ground_level, lower_body_grounded = lower_body_on_ground(landmarks, check_knee_angles=True)

            lknee, rknee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value], landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value]
            lankle, rankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value], landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value]
            lfoot, rfoot = landmarks[mp_pose.PoseLandmark.LEFT_FOOT_INDEX.value], landmarks[mp_pose.PoseLandmark.RIGHT_FOOT_INDEX.value]

            l_angle = calculate_angle_between_landmarks(lknee, lankle, lfoot)
            r_angle = calculate_angle_between_landmarks(rknee, rankle, rfoot)

            self.pose_tracker.update(lower_body_grounded, l_angle, r_angle)

            if self.pose_tracker.relax_pose and not self.pose_tracker.stretch_pose:
                self.check_timer = False

            if self.pose_tracker.relax_pose and self.pose_tracker.stretch_pose:
                self._handle_pose_hold(frame)

            self._draw_info(frame, l_angle, r_angle, lower_body_grounded, pose_landmarks, display)

            if display:
                cv2.imshow("Ankle Toe Movement Exercise", frame)
            
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
            self.old_time = time.time()
            self.check_timer = True
            print("[AnkleToe] time for raise", self.old_time)
        else:
            cur_time = time.time()
            if cur_time - self.old_time > self.hold_secs:
                self.count += 1
                self.pose_tracker.reset()
                self.check_timer = False
                announceForCount(self.count)
            else:
                cv2.putText(
                    frame,
                    f"hold pose: {self.hold_secs - cur_time + self.old_time:.2f}",
                    (250, 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (255, 0, 0),
                    2,
                )

    def _draw_info(self, frame, l_angle, r_angle, lower_body_grounded, pose_landmarks, display):
        """Draw exercise information using the shared renderer."""
        debug_info = None
        if self.debug:
            debug_info = {
                'lower_body_on_ground': lower_body_grounded,
                'relax Pose': self.pose_tracker.relax_pose,
                'stretch Pose': self.pose_tracker.stretch_pose,
                'stretch angle': (l_angle, r_angle)
            }
        
        exercise_state = ExerciseState(
            count=self.count,
            debug=self.debug,
            render_all=self.render_all,
            exercise_name="Ankle Toe Movement",
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
    tracker = AnkleToeMovementTracker()
    tracker.start()
