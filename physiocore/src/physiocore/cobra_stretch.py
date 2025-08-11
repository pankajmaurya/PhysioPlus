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
                                lower_body_on_ground)

# Handy aliases
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

debug, video, render_all, save_video, lenient_mode = flags.parse_flags()

HOLD_SECS=3

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
    
    def updateTracker(self,angle_left_elb, angle_right_elb, raise_angle, wrist_close,wrist_near_torse, head_angle, lower_body_prone):
        if not self.resting_pose:
            lenient = True if lenient_mode else  (wrist_close and wrist_near_torse and head_angle < 100)
            self.resting_pose = (lenient  and lower_body_prone and (angle_left_elb < 60 
                                 or angle_right_elb < 60) and raise_angle >165)
            self.raise_pose = False

        if self.resting_pose:
            lenient = True if lenient_mode else  (wrist_close and head_angle > 125)
            self.raise_pose = (lenient  and lower_body_prone and (angle_left_elb > 120 
                               or angle_right_elb > 120) and raise_angle < 150)
    
    def resetTracker(self):
        self.resting_pose = False
        self.raise_pose = False

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
    
    ground_level,on_ground = lower_body_on_ground(landmarks)

    # Identify keypoints
    lhip, rhip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value], landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value]
    lshoulder, rshoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value], landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
    lwrist, rwrist = landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value], landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value]
    lelbow, relbow = landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value], landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value]
    lknee, rknee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value], landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value]
    nose = landmarks[mp_pose.PoseLandmark.NOSE.value]

    angle_left_elb = calculate_angle_between_landmarks(lshoulder,lelbow,lwrist)
    angle_right_elb = calculate_angle_between_landmarks(rshoulder,relbow,rwrist)

    shoulder_mid_point = calculate_mid_point((lshoulder.x, lshoulder.y),(rshoulder.x, rshoulder.y))
    hip_mid_point = calculate_mid_point((lhip.x, lhip.y),(rhip.x, rhip.y))
    #knee_mid_point = calculate_mid_point((lknee.x, lknee.y),(rknee.x, rknee.y))
    wrist_mid_point = calculate_mid_point((lwrist.x, lwrist.y),(rwrist.x, rwrist.y))

    nose_coordinates = (nose.x, nose.y)
    knee = lknee if (lknee.visibility > rknee.visibility) else rknee  
    raise_angle = calculate_angle(shoulder_mid_point,hip_mid_point,(knee.x, knee.y))
    head_angle = calculate_angle(nose_coordinates, shoulder_mid_point, wrist_mid_point)


    r_wrist_close = abs(ground_level -rwrist.y) < 0.1  # Check if ankle is near ground
    l_wrist_close = abs(ground_level - lwrist.y) < 0.1

    r_wrist_near_torse = between(lshoulder.x,lwrist.x,lhip.x) # check if wrist is near torso
    l_wrist_near_torse = between(rshoulder.x,rwrist.x,rhip.x)


    feet_orien = detect_feet_orientation(landmarks)
    
    lower_body_prone = on_ground and (feet_orien == "Feet are downwards" or feet_orien == "either feet is downward")

    hold_reached = False  
    
    # Update pose tracking state
    pose_tracker.updateTracker(angle_left_elb, angle_right_elb, raise_angle, l_wrist_close and r_wrist_close,
                               l_wrist_near_torse and r_wrist_near_torse, head_angle, lower_body_prone)

    if pose_tracker.resting_pose and not pose_tracker.raise_pose:
        check_timer = False

    # If all conditions are met, increment count and reset tracking state
    if pose_tracker.resting_pose and pose_tracker.raise_pose:
        if not check_timer:
            s_time=time.time()
            check_timer=True
            print("time for raise", s_time)
        elif check_timer:
            cur_time = time.time()
            if cur_time - s_time > HOLD_SECS:
                count+=1
                pose_tracker.resetTracker()
                check_timer=False
                Thread(target=announce).start()
            else:
                print("Continue holding")
                cv2.putText(frame, f'hold : {HOLD_SECS - cur_time + s_time:.2f}', (250, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
    
    # Display count on screen
    cv2.putText(frame, f'Count: {count}', (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
    
    # Debug mode: Show key variables on screen
    if debug:
        # cv2.putText(frame, f'Lying Down: {lying_down}', (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f'Resting Pose: {pose_tracker.resting_pose}', (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f'Raise Pose: {pose_tracker.raise_pose}', (10, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f'lowerbody grounded: {lower_body_prone}', (10, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f'elbow angle(L,R): {angle_left_elb:.2f}, {angle_right_elb:.2f}', (10, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f'wrist close: {l_wrist_close and r_wrist_close}', (10, 230), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f'wrist near torse: {l_wrist_near_torse and r_wrist_near_torse}', (10, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f'head angle: {head_angle:.2f}', (10, 290), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f'raise angle: {raise_angle:.2f}', (10, 320), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f'feet orientation: {feet_orien}', (10, 350), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

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
    cv2.namedWindow('Cobra Strech Exercise',cv2.WINDOW_NORMAL)
    cv2.imshow('Cobra Strech Exercise', frame)
    
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