from . import basic_math as basic_math
import mediapipe as mp
import numpy as np

mp_pose = mp.solutions.pose

# Calculate angle beyween 3 landmarks
def calculate_angle_between_landmarks(lm1,lm2,lm3):
    a = (lm1.x,lm1.y)
    b = (lm2.x,lm2.y)
    c = (lm3.x,lm3.y)
    return(basic_math.calculate_angle(a,b,c))

# Calculate midpoint of two points
def calculate_mid_point_landmarks(lm1,lm2):
    a = (lm1.x, lm1.y)
    b = (lm2.x,lm2.y)
    return(basic_math.calculate_mid_point(a,b))

# This does not handle the case when the feet are level, see images/back-isometric-rest1.png as a testcase.
def detect_feet_orientation(landmarks):
    lankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value]
    lfoot_ind = landmarks[mp_pose.PoseLandmark.LEFT_FOOT_INDEX.value]
    rankle = landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value]
    rfoot_ind = landmarks[mp_pose.PoseLandmark.RIGHT_FOOT_INDEX.value]
    lheel = landmarks[mp_pose.PoseLandmark.LEFT_HEEL.value]
    rheel = landmarks[mp_pose.PoseLandmark.RIGHT_HEEL.value]

    if (lfoot_ind.y > lheel.y and lankle.y > lheel.y) and (rfoot_ind.y > rheel.y and rankle.y > rheel.y):
        return "Feet are downwards"
    if (lfoot_ind.y > lheel.y and lankle.y > lheel.y) or (rfoot_ind.y > rheel.y and rankle.y > rheel.y):
        return "either feet is downward"
    if (lfoot_ind.y < lheel.y and lankle.y < lheel.y) and (rfoot_ind.y < rheel.y and rankle.y < rheel.y):
        return "feet are upward"
    if (lfoot_ind.y < lheel.y and lankle.y < lheel.y) or (rfoot_ind.y < rheel.y and rankle.y < rheel.y):
        return "either feet are upward"
    
    return "Undetected Pose"



def upper_body_is_lying_down(landmarks):
    """Check if the patient is lying down by analyzing upper body landmarks."""
    """assumptions is person should be parallel to x-axis and perpendicular to Y-axis when laying down"""
    left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
    right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
    left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]
    right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value]

    # Compute shoulder and hip midpoints
    shoulder_mid = calculate_mid_point_landmarks(left_shoulder, right_shoulder)
    hip_mid = calculate_mid_point_landmarks(left_hip, right_hip)
    
    # Calculate torso length 
    torso_length = np.sqrt((shoulder_mid[0] - hip_mid[0]) ** 2 + (shoulder_mid[1] - hip_mid[1]) ** 2)
   
    # Ground level calculation (MAX Y value excluding hands)
    body_landmarks = [
        mp_pose.PoseLandmark.LEFT_EAR.value, mp_pose.PoseLandmark.RIGHT_EAR.value,
        mp_pose.PoseLandmark.LEFT_SHOULDER.value,mp_pose.PoseLandmark.RIGHT_SHOULDER.value,
        mp_pose.PoseLandmark.LEFT_HIP.value, mp_pose.PoseLandmark.RIGHT_HIP.value
    ]

    ground_level = max([landmarks[lm].y for lm in body_landmarks])

    tolerance = 0.9 * torso_length - 0.015
    # Check if the person is lying down
    #max_y_distance = max(abs(landmarks[lm].y - ground_level) for lm in body_landmarks)
    lying_down = all(abs(landmarks[lm].y - ground_level) <= tolerance for lm in body_landmarks)
    
    return ground_level,lying_down


def lower_body_on_ground(landmarks, check_knee_angles=False):
    """assumptions is person should be parallel to x-axis and perpendicular to Y-axis when laying down"""
    left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
    right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
    left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]
    right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value]
    lknee, rknee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value], landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value]
    lankle, rankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value], landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value]
    
    l_knee_angle = calculate_angle_between_landmarks(left_hip, lknee, lankle)
    r_knee_angle = calculate_angle_between_landmarks(right_hip, rknee, rankle)

    # Compute shoulder and hip midpoints
    shoulder_mid = calculate_mid_point_landmarks(left_shoulder, right_shoulder)
    hip_mid = calculate_mid_point_landmarks(left_hip, right_hip)
    
    # Calculate torso length 
    torso_length = np.sqrt((shoulder_mid[0] - hip_mid[0]) ** 2 + (shoulder_mid[1] - hip_mid[1]) ** 2)
   
    # Ground level calculation (MAX Y value excluding hands)
    body_landmarks = [
        mp_pose.PoseLandmark.LEFT_HIP.value, mp_pose.PoseLandmark.RIGHT_HIP.value,
        mp_pose.PoseLandmark.LEFT_KNEE.value, mp_pose.PoseLandmark.RIGHT_KNEE.value,
        mp_pose.PoseLandmark.LEFT_ANKLE.value,mp_pose.PoseLandmark.RIGHT_ANKLE.value
    ]

    ground_level = max([landmarks[lm].y for lm in body_landmarks])

    tolerance = 0.923 * torso_length - 0.015
    # Check if the person is lying down
    #max_y_distance = max(abs(landmarks[lm].y - ground_level) for lm in body_landmarks)
    knee_straight = basic_math.between(150,l_knee_angle,180) or basic_math.between(150,r_knee_angle,180)
    knee_check_passed = knee_straight if check_knee_angles else True
    on_ground = all(abs(landmarks[lm].y - ground_level) <= tolerance for lm in body_landmarks) and knee_check_passed
    
    return ground_level,on_ground

def distance(point1, point2):
    """Calculate Euclidean distance between two points."""
    return np.sqrt((point1.x - point2.x) ** 2 + (point1.y - point2.y) ** 2)
