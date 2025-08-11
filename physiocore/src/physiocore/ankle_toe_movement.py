import json
import os
import time
from threading import Thread
import cv2
import mediapipe as mp

from physiocore.lib import flags, graphics_utils, mp_utils
from physiocore.lib.basic_math import between
from physiocore.lib.file_utils import announce, create_output_files, release_files
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
        self.debug, self.video, self.render_all, self.save_video, self.lenient_mode = flags.parse_flags()
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
        self.cap = cv2.VideoCapture(self.video if self.video else 0)
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

            self._draw_info(frame, l_angle, r_angle, lower_body_grounded, pose_landmarks)

            cv2.imshow("Ankle Toe Movement Exercise", frame)
            if self.save_video and self.debug:
                self.output_with_info.write(frame)

            key = cv2.waitKey(delay) & 0xFF
            if key == ord("q"):
                break
            elif key == ord("p"):
                self._pause_loop()

        self._cleanup()

    def _handle_pose_hold(self, frame):
        if not self.check_timer:
            self.old_time = time.time()
            self.check_timer = True
            print("time for raise", self.old_time)
        else:
            cur_time = time.time()
            if cur_time - self.old_time > self.hold_secs:
                self.count += 1
                self.pose_tracker.reset()
                self.check_timer = False
                Thread(target=announce).start()
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

    def _draw_info(self, frame, l_angle, r_angle, lower_body_grounded, pose_landmarks):
        cv2.putText(frame, f"Count: {self.count}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

        if self.debug:
            cv2.putText(frame, f"lower_body_on_ground: {lower_body_grounded}", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, f"relax Pose: {self.pose_tracker.relax_pose}", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, f"stretch Pose: {self.pose_tracker.stretch_pose}", (10, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, f"stretch angle: {l_angle:.2f}, {r_angle:.2f}", (10, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        if self.render_all:
            custom_connections, custom_style, connection_spec = graphics_utils.get_default_drawing_specs("all")
        else:
            custom_connections, custom_style, connection_spec = graphics_utils.get_default_drawing_specs("")

        mp_drawing.draw_landmarks(
            frame,
            pose_landmarks,
            connections=custom_connections,
            connection_drawing_spec=connection_spec,
            landmark_drawing_spec=custom_style,
        )

    def _pause_loop(self):
        while True:
            key = cv2.waitKey(0) & 0xFF
            if key == ord("r"):
                break
            elif key == ord("q"):
                self._cleanup()
                exit()

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
