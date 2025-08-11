import json
import os
import time
from threading import Thread

import cv2
import mediapipe as mp
import numpy as np

from . import flags as flags
from . import graphics_utils as graphics_utils
from . import mp_utils as mp_utils
from .lib.basic_math import (between, calculate_angle,
                            calculate_mid_point)
from .lib.file_utils import (announce, create_output_files,
                            release_files)
from .lib.landmark_utils import (calculate_angle_between_landmarks,
                                detect_feet_orientation,
                                upper_body_is_lying_down)
from .lib.mp_utils import pose2

# Handy aliases
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

debug, video, render_all, save_video , lenient_mode = flags.parse_flags()

jconfig = None
# Get the directory containing the script
script_dir = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(script_dir, "json", "any_prone_straight_leg_raise.json")

jconfig = None
try:
    with open(json_path) as conf:
        r = conf.read()
        if r:
            jconfig = json.loads(r)
except FileNotFoundError:
    print("Config file not found, using default values")

knee_angle_min=150
knee_angle_max=180
rest_pose_raise_angle_min=160
rest_pose_raise_angle_max=180
raise_pose_raise_angle_min=100
raise_pose_raise_angle_max=140
HOLD_SECS=5

if jconfig and jconfig['knee_angle_min']:
    knee_angle_min = jconfig['knee_angle_min']
if jconfig and jconfig['knee_angle_max']:
    knee_angle_max = jconfig['knee_angle_max']
if jconfig and jconfig['rest_pose_raise_angle_min']:
    rest_pose_raise_angle_min = jconfig['rest_pose_raise_angle_min']
if jconfig and jconfig['rest_pose_raise_angle_max']:
    rest_pose_raise_angle_max = jconfig['rest_pose_raise_angle_max']
if jconfig and jconfig['raise_pose_raise_angle_min']:
    raise_pose_raise_angle_min = jconfig['raise_pose_raise_angle_min']
if jconfig and jconfig['raise_pose_raise_angle_max']:
    raise_pose_raise_angle_max = jconfig['raise_pose_raise_angle_max']
if jconfig and jconfig['HOLD_SECS']:
    HOLD_SECS = jconfig['HOLD_SECS']

# Capture video
cap = cv2.VideoCapture(video if video else 0)
# Get input FPS
input_fps = int(cap.get(cv2.CAP_PROP_FPS))
# If webcam returns 0 fps, default to 30
if input_fps <= 0:
    input_fps = 30
delay = int(1000 / input_fps)

class PoseTracker:
    def __init__(self):  
        self.l_resting_pose = False
        self.r_resting_pose = False
        self.l_raise_pose = False
        self.r_raise_pose = False
    
    def updateTracker(self, prone_lying_down, l_knee_angle, r_knee_angle, l_ankle_close, r_ankle_close, l_raise_angle, r_raise_angle,lknee_high,rknee_high):
        if not self.l_resting_pose:
            lenient = True if lenient_mode else  (r_ankle_close and between(knee_angle_min,r_knee_angle,knee_angle_max))
            self.l_resting_pose = lenient and prone_lying_down and l_ankle_close and between(knee_angle_min,l_knee_angle,knee_angle_max) and between(rest_pose_raise_angle_min,l_raise_angle, rest_pose_raise_angle_max)
            self.l_raise_pose = False

        if not self.r_resting_pose:
            lenient = True if lenient_mode else  (l_ankle_close and between(knee_angle_min,l_knee_angle,knee_angle_max))
            self.r_resting_pose = lenient and prone_lying_down and r_ankle_close and between(knee_angle_min,r_knee_angle,knee_angle_max) and between(rest_pose_raise_angle_min, r_raise_angle, rest_pose_raise_angle_max)
            self.r_raise_pose = False

        # Raise pose condition: operative leg lifted + hold reached
        if self.l_resting_pose :
            lenient = True if lenient_mode else  (r_ankle_close and between(knee_angle_min,r_knee_angle,knee_angle_max))
            if lenient and prone_lying_down and lknee_high and between(raise_pose_raise_angle_min,l_raise_angle,raise_pose_raise_angle_max) and between(knee_angle_min, l_knee_angle, knee_angle_max):
                self.l_raise_pose = True
            else:
                self.l_raise_pose = False

        # Raise pose condition: operative leg lifted + hold reached
        if self.r_resting_pose:
            lenient = True if lenient_mode else  (l_ankle_close and between(knee_angle_min,l_knee_angle,knee_angle_max))
            if lenient and prone_lying_down and rknee_high and between(raise_pose_raise_angle_min,r_raise_angle, raise_pose_raise_angle_max) and between(knee_angle_min, r_knee_angle, knee_angle_max):
                self.r_raise_pose = True
            else:
                self.r_raise_pose = False
    
    def resetTracker(self):
        self.l_raise_pose = False
        self.r_raise_pose = False
        self.l_resting_pose = False
        self.r_resting_pose = False

# Ask user for operative leg
pose_tracker = PoseTracker()
count = 0

if save_video:
    output, output_with_info = create_output_files(cap, save_video)

l_check_timer=False
r_check_timer=False
while True:
    # Process frame and extract pose landmarks
    success, landmarks, frame, pose_landmarks = mp_utils.processFrameAndGetLandmarks(cap, pose2)

    if not success:
        break
    
    if frame is None:
        print("Skipping empty frame...")
        continue  # Skip this frame and try the next one

    if save_video:
        output.write(frame)
    
    if not pose_landmarks:
        continue  # Skip if no pose landmarks detected
    
    ground_level,lying_down = upper_body_is_lying_down(landmarks)
    feet_orien = detect_feet_orientation(landmarks)

    # Identify keypoints
    lshoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
    rshoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
    shoulder_mid_point = calculate_mid_point((lshoulder.x, lshoulder.y),
                                             (rshoulder.x, rshoulder.y))
    lhip, rhip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value], landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value]
    lknee, rknee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value], landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value]
    lankle, rankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value], landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value]
    lshld,rshld = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value], landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
    lheel, rheel = landmarks[mp_pose.PoseLandmark.LEFT_HEEL.value], landmarks[mp_pose.PoseLandmark.RIGHT_HEEL.value]
    
    l_knee_angle = calculate_angle_between_landmarks(lhip, lknee, lankle)
    r_knee_angle = calculate_angle_between_landmarks(rhip, rknee, rankle)
    l_raise_angle = calculate_angle((shoulder_mid_point[0],shoulder_mid_point[1]),(lhip.x,lhip.y),(lankle.x,lankle.y))
    r_raise_angle = calculate_angle((shoulder_mid_point[0],shoulder_mid_point[1]),(rhip.x,rhip.y),(rankle.x,rankle.y))    
    r_ankle_close = abs(ground_level -rankle.y) < 0.1  # Check if ankle is near ground
    l_ankle_close = abs(ground_level - lankle.y) < 0.1  # Check if ankle is near ground
    lknee_high = lheel.y < lshld.y
    rknee_high = rheel.y < rshld.y
    
    hold_reached = False  
    
    prone_lying_down = lying_down and (feet_orien == "Feet are downwards" or feet_orien == "either feet is downward")
    
    # Update pose tracking state
    pose_tracker.updateTracker(prone_lying_down, l_knee_angle, r_knee_angle, l_ankle_close, r_ankle_close, l_raise_angle, r_raise_angle,lknee_high,rknee_high)
    
    if pose_tracker.l_resting_pose and not pose_tracker.l_raise_pose:
        l_check_timer = False
    if pose_tracker.r_resting_pose and not pose_tracker.r_raise_pose:
        r_check_timer = False

    # If all conditions are met, increment count and reset tracking state
    if prone_lying_down and pose_tracker.l_resting_pose and pose_tracker.l_raise_pose:
        if not l_check_timer:
            l_time=time.time()
            l_check_timer=True
            print("time for left raise", l_time)
        elif l_check_timer:
            cur_l_time = time.time()
            if cur_l_time - l_time > HOLD_SECS:
                count+=1
                pose_tracker.resetTracker()
                l_check_timer=False
                Thread(target=announce).start()
            else:
                print("Continue holding left leg")
                cv2.putText(frame, f'hold left leg: {HOLD_SECS - cur_l_time + l_time:.2f}', (250, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
        
        
    if prone_lying_down and pose_tracker.r_resting_pose and pose_tracker.r_raise_pose:
        if not r_check_timer:
            r_time=time.time()
            r_check_timer=True
            print("time for right raise", r_time)
        elif r_check_timer:
            cur_r_time = time.time()
            if cur_r_time - r_time > HOLD_SECS:
                count+=1
                pose_tracker.resetTracker()
                r_check_timer=False
                Thread(target=announce).start()
            else:
                print("Continue holding right leg")
                cv2.putText(frame, f'hold right leg: {HOLD_SECS - cur_r_time + r_time:.2f}', (250, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
    
    # Display count on screen
    cv2.putText(frame, f'Count: {count}', (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
    
    # Debug mode: Show key variables on screen
    if debug:
        cv2.putText(frame, f'Prone Lying Down: {prone_lying_down}', (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f'Resting Pose: {pose_tracker.l_resting_pose}, {pose_tracker.r_resting_pose}', (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f'Raise Pose: {pose_tracker.l_raise_pose}, {pose_tracker.r_raise_pose}', (10, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f'Ankle floored: {l_ankle_close}, {r_ankle_close}', (10, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f'Knee Angles: {l_knee_angle:.2f}, {r_knee_angle:.2f}', (10, 230), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(frame, f'Raise angle: {l_raise_angle:.2f}, {r_raise_angle:.2f}', (10, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    # Draw pose landmarks
    if render_all:
        custom_connections, custom_style, connection_spec = graphics_utils.get_default_drawing_specs('all')
    else:    
        custom_connections, custom_style, connection_spec = graphics_utils.get_default_drawing_specs('')
    
    # Draw pose landmarks and connections
    mp_drawing.draw_landmarks(
        frame,
        pose_landmarks,
        connections = custom_connections, #  passing the modified connections list
        connection_drawing_spec = connection_spec,  # and drawing styles
        landmark_drawing_spec = custom_style)
    cv2.namedWindow('Any Prone SLR Exercise', cv2.WINDOW_NORMAL)
    cv2.imshow('Any Prone SLR Exercise', frame)
    
    if save_video:
        output_with_info.write(frame)
    
    key = cv2.waitKey(delay) & 0xFF
    # Break on 'q' key press
    if key ==  ord('q') :
        break
    elif key == ord('p'):
        while True:
            key = cv2.waitKey(0) & 0xFF  # Wait indefinitely
            if key == ord('r'):  # Press 'r' to resume
                break  # Exit the pause loop
            elif key == ord('q'):  # Press 'q' to quit during pause
                cap.release()
                cv2.destroyAllWindows()
                exit()  # Exit the program

cap.release()
if save_video:
    release_files(output, output_with_info)
    
print(f"Final count: {count}")
