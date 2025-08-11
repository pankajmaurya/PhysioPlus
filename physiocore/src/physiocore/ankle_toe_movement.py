import json
import os
import time
from threading import Thread

import cv2
import mediapipe as mp

from . import flags as flags
from . import graphics_utils as graphics_utils
from . import mp_utils as mp_utils
from .lib.basic_math import between
from .lib.file_utils import (announce, create_output_files,
                            release_files)
from .lib.landmark_utils import (calculate_angle_between_landmarks,
                                lower_body_on_ground)
from .lib.mp_utils import pose2

# Handy aliases
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

debug, video, render_all, save_video, lenient_mode = flags.parse_flags()

# Get the directory containing the script
script_dir = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(script_dir, "json", "ankle_toe_movement.json")

jconfig = None
try:
    with open(json_path) as conf:
        r = conf.read()
        if r:
            jconfig = json.loads(r)
except FileNotFoundError:
    print("Config file not found, using default values")

relax_ankle_angle_min=80
relax_ankle_angle_max=110
stretch_ankle_angle_min=140
stretch_ankle_angle_max=180
HOLD_SECS=2
if jconfig and jconfig['relax_ankle_angle_min']:
    relax_ankle_angle_min = jconfig['relax_ankle_angle_min']
if jconfig and jconfig['relax_ankle_angle_max']:
    relax_ankle_angle_max = jconfig['relax_ankle_angle_max']
if jconfig and jconfig['stretch_ankle_angle_min']:
    stretch_ankle_angle_min = jconfig['stretch_ankle_angle_min']
if jconfig and jconfig['stretch_ankle_angle_max']:
    stretch_ankle_angle_max = jconfig['stretch_ankle_angle_max']
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
        self.relax_pose = False
        self.stretch_pose = False
    
    def updateTracker(self, lower_body_grounded, l_ankle_stretch_angle, r_ankle_stretch_angle):
        if not self.relax_pose:
            self.relax_pose = (lower_body_grounded and  
                                 between(relax_ankle_angle_min,l_ankle_stretch_angle, relax_ankle_angle_max) and 
                                 between(relax_ankle_angle_min,r_ankle_stretch_angle, relax_ankle_angle_max) )
            self.stretch_pose = False

        if self.relax_pose:
            l_ankle_stretched = between(stretch_ankle_angle_min, l_ankle_stretch_angle, stretch_ankle_angle_max)  
            r_ankle_stretched = between(stretch_ankle_angle_min, r_ankle_stretch_angle, stretch_ankle_angle_max)  
            ankles_stretched_lenient = l_ankle_stretched or r_ankle_stretched
            ankles_stretched_strict = l_ankle_stretched and r_ankle_stretched
            ankles_stretched = ankles_stretched_lenient if lenient_mode else ankles_stretched_strict

            if lower_body_grounded and ankles_stretched:
                self.stretch_pose = True
            else:
                self.stretch_pose = False

    def resetTracker(self):
        self.relax_pose = False
        self.stretch_pose = False

# Ask user for operative leg
pose_tracker = PoseTracker()
count = 0

if save_video:
    output, output_with_info = create_output_files(cap, save_video)

check_timer=False
while True:
    # Process frame and extract pose landmarks
    success, landmarks, frame, pose_landmarks = mp_utils.processFrameAndGetLandmarks(cap,pose2)

    if not success:
        break
    
    if frame is None:
        print("Skipping empty frame...")
        continue  # Skip this frame and try the next one

    if save_video:
        output.write(frame)
    
    if not pose_landmarks:
        continue  # Skip if no pose landmarks detected
    
    ground_level, lower_body_grounded = lower_body_on_ground(landmarks, check_knee_angles=True)
    
    # Identify keypoints
    lknee, rknee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value], landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value]
    lankle, rankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value], landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value]
    l_foot_index, r_foot_index = landmarks[mp_pose.PoseLandmark.LEFT_FOOT_INDEX.value], landmarks[mp_pose.PoseLandmark.RIGHT_FOOT_INDEX.value]
   
    l_ankle_stretch_angle = calculate_angle_between_landmarks(lknee, lankle, l_foot_index)
    r_ankle_stretch_angle = calculate_angle_between_landmarks(rknee, rankle, r_foot_index)    
    
    
    # Update pose tracking state
    pose_tracker.updateTracker(lower_body_grounded, l_ankle_stretch_angle, r_ankle_stretch_angle)

    if pose_tracker.relax_pose and not pose_tracker.stretch_pose:
        check_timer = False

    # If all conditions are met, increment count and reset tracking state
    if pose_tracker.relax_pose and pose_tracker.stretch_pose:
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
        cv2.putText(frame, f'lower_body_on_ground: {lower_body_grounded}', (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f'relax Pose: {pose_tracker.relax_pose}', (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f'stretch Pose: {pose_tracker.stretch_pose}', (10, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f'stretch angle: {l_ankle_stretch_angle:.2f}, {r_ankle_stretch_angle:.2f}', (10, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

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
    cv2.namedWindow('Ankle Toe Movement Exercise',cv2.WINDOW_NORMAL)
    cv2.imshow('Ankle Toe Movement Exercise', frame)
    
    if save_video and debug:
        output_with_info.write(frame)
    
    key = cv2.waitKey(delay) & 0xFF
    # Break on 'q' key pres
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