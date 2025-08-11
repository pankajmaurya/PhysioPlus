import json
import os
import time
from threading import Thread

import cv2
import mediapipe as mp
import numpy as np

from .lib import flags
from .lib import graphics_utils
from .lib import mp_utils
from .lib.basic_math import (
    between,
    calculate_angle,
    calculate_mid_point
)
from .lib.file_utils import (
    announce,
    create_output_files,
    release_files
)
from .lib.landmark_utils import (
    calculate_angle_between_landmarks,
    upper_body_is_lying_down
)

"""
from . import flags as flags
from . import graphics_utils as graphics_utils
from . import mp_utils as mp_utils
from .lib.basic_math import (between, calculate_angle,
                            calculate_mid_point)
from .lib.file_utils import (announce, create_output_files,
                            release_files)
from .lib.landmark_utils import (calculate_angle_between_landmarks,
                                upper_body_is_lying_down)
"""
# Handy aliases
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

debug, video, render_all, save_video, lenient_mode = flags.parse_flags()

# Get the directory containing the script
script_dir = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(script_dir, "json", "bridging.json")

jconfig = None
try:
    with open(json_path) as conf:
        r = conf.read()
        if r:
            jconfig = json.loads(r)
except FileNotFoundError:
    print("Config file not found, using default values")

knee_angle_min=40
knee_angle_max=90
rest_angle_min=100
rest_angle_max=130
raise_angle_min=155
raise_angle_max=180
HOLD_SECS=5

if jconfig and jconfig['knee_angle_min']:
    knee_angle_min = jconfig['knee_angle_min']
if jconfig and jconfig['knee_angle_max']:
    knee_angle_max = jconfig['knee_angle_max']
if jconfig and jconfig['rest_angle_min']:
    rest_angle_min = jconfig['rest_angle_min']
if jconfig and jconfig['rest_angle_max']:
    rest_angle_max = jconfig['rest_angle_max']
if jconfig and jconfig['raise_angle_min']:
    raise_angle_min = jconfig['raise_angle_min']
if jconfig and jconfig['raise_angle_max']:
    raise_angle_max = jconfig['raise_angle_max']
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
        self.resting_pose = False
        self.raise_pose = False
    
    def updateTracker(self, lying_down, l_knee_angle, r_knee_angle, l_ankle_close, r_ankle_close, l_raise_angle, r_raise_angle):
        if not self.resting_pose:
            lenient =  True if lenient_mode else (l_ankle_close and r_ankle_close and between(knee_angle_min,r_knee_angle,knee_angle_max) 
                                 and between(knee_angle_min,l_knee_angle,knee_angle_max) and between(rest_angle_min, l_raise_angle, rest_angle_max)
                                 and between(rest_angle_min, r_raise_angle, rest_angle_max))
            self.resting_pose = (lenient and lying_down and (l_ankle_close or r_ankle_close) and (between(knee_angle_min,r_knee_angle,knee_angle_max) 
                                 or between(knee_angle_min,l_knee_angle,knee_angle_max)) and (between(rest_angle_min, l_raise_angle, rest_angle_max)
                                 or between(rest_angle_min, r_raise_angle, rest_angle_max)))
            self.raise_pose = False

        # Raise pose condition: operative leg lifted + hold reached
        if self.resting_pose:
            lenient = True if lenient_mode else (between(raise_angle_min, l_raise_angle, raise_angle_max) and between(raise_angle_min, r_raise_angle, raise_angle_max) 
                and between(knee_angle_min,r_knee_angle,knee_angle_max) and between(knee_angle_min,l_knee_angle,knee_angle_max))
            if (lenient and (between(raise_angle_min, l_raise_angle, raise_angle_max) or between(raise_angle_min, r_raise_angle, raise_angle_max)) 
                and (between(knee_angle_min,r_knee_angle,knee_angle_max) or between(knee_angle_min,l_knee_angle,knee_angle_max))):
                self.raise_pose = True
            else:
                self.raise_pose = False
    
    def resetTracker(self):
        self.raise_pose = False
        self.resting_pose = False

# Ask user for operative leg
pose_tracker = PoseTracker()
count = 0

if save_video:
    output, output_with_info = create_output_files(cap, save_video)

check_timer=False
while True:
    # Process frame and extract pose landmarks
    success, landmarks, frame, pose_landmarks = mp_utils.processFrameAndGetLandmarks(cap)

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
    
    # Identify keypoints
    lshoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
    rshoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
    shoulder_mid_point = calculate_mid_point((lshoulder.x, lshoulder.y),
                                             (rshoulder.x, rshoulder.y))

    lhip, rhip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value], landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value]
    lknee, rknee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value], landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value]
    lankle, rankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value], landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value]
    lshld,rshld = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value], landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
    
    l_knee_angle = calculate_angle_between_landmarks(lhip, lknee, lankle)
    r_knee_angle = calculate_angle_between_landmarks(rhip, rknee, rankle)
    l_raise_angle = calculate_angle((lshoulder.x,lshoulder.y),(lhip.x,lhip.y),(lknee.x,lknee.y))
    r_raise_angle = calculate_angle((rshoulder.x,rshoulder.y),(rhip.x,rhip.y),(rknee.x,rknee.y))    
    r_ankle_close = abs(ground_level -rankle.y) < 0.1  # Check if ankle is near ground
    l_ankle_close = abs(ground_level - lankle.y) < 0.1  # Check if ankle is near ground
    
    hold_reached = False  # Placeholder: Implement actual hold logic
    
    # Update pose tracking state
    pose_tracker.updateTracker(lying_down, l_knee_angle, r_knee_angle, l_ankle_close, r_ankle_close, l_raise_angle, r_raise_angle)

    if pose_tracker.resting_pose and not pose_tracker.raise_pose:
        check_timer = False

    # If all conditions are met, increment count and reset tracking state
    if pose_tracker.resting_pose and pose_tracker.raise_pose:
        if not check_timer:
            old_time=time.time()
            check_timer=True
            print("time for raise", old_time)
        elif check_timer:
            cur_time = time.time()
            if cur_time - old_time > HOLD_SECS:
                count+=1
                pose_tracker.resetTracker()
                check_timer=False
                Thread(target=announce).start()
            else:
                print("Continue holding pose")
                cv2.putText(frame, f'hold pose: {HOLD_SECS - cur_time + old_time:.2f}', (250, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
        
        
    # Display count on screen
    cv2.putText(frame, f'Count: {count}', (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
    
    # Debug mode: Show key variables on screen
    if debug:
        cv2.putText(frame, f'Lying Down: {lying_down}', (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f'Resting Pose: {pose_tracker.resting_pose}', (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f'Raise Pose: {pose_tracker.raise_pose}', (10, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
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
    cv2.namedWindow('Bridging Exercise',cv2.WINDOW_NORMAL)
    cv2.imshow('Bridging Exercise', frame)
    
    if save_video and debug:
        output_with_info.write(frame)
    
    key = cv2.waitKey(delay) & 0xFF
    # Break on 'q' key press
    if key ==  ord('q') :
        break
    # TODO: Make this pause/resume assessment work. This code works for CatCow video.
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
