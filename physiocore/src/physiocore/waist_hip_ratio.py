import cv2
import mediapipe as mp
import numpy as np
import math

class WaistHipRatioCalculator:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=2,
            enable_segmentation=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils
        
    def calculate_distance(self, point1, point2):
        """Calculate Euclidean distance between two points"""
        return math.sqrt((point1.x - point2.x)**2 + (point1.y - point2.y)**2)
    
    def get_waist_hip_measurements(self, landmarks):
        """
        Extract waist and hip measurements from pose landmarks
        For side pose, we use:
        - Waist: narrowest point between ribs and hips (approximated using shoulder-hip midpoint)
        - Hip: widest point around hip area
        """
        # Get relevant landmarks
        left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
        left_hip = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value]
        right_hip = landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value]
        
        # For side pose, we'll use the visible side (assume left side is visible)
        # You may need to adjust this based on which side is facing the camera
        
        # Waist approximation: point between shoulder and hip on the torso
        # This is a simplified approach - in reality, waist is narrowest point
        waist_y = left_shoulder.y + 0.6 * (left_hip.y - left_shoulder.y)
        waist_point = type('Point', (), {
            'x': left_shoulder.x + 0.3 * (left_hip.x - left_shoulder.x),
            'y': waist_y,
            'z': left_shoulder.z
        })()
        
        # Hip measurement: use the hip landmarks directly
        hip_width = self.calculate_distance(left_hip, right_hip)
        
        # For waist, we need to estimate the width
        # This is challenging from a single side view
        # We'll use a proportion based on the torso depth
        torso_depth = abs(left_shoulder.z - left_hip.z)
        estimated_waist_width = torso_depth * 0.8  # Approximation factor
        
        return estimated_waist_width, hip_width, waist_point
    
    def process_frame(self, frame):
        """Process a single frame and return WHR if person detected"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(rgb_frame)
        
        if results.pose_landmarks:
            # Draw pose landmarks
            self.mp_drawing.draw_landmarks(
                frame, results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS)
            
            # Calculate measurements
            waist_width, hip_width, waist_point = self.get_waist_hip_measurements(
                results.pose_landmarks.landmark
            )
            
            # Calculate ratio
            if hip_width > 0:
                whr = waist_width / hip_width
                
                # Draw measurement lines and text
                h, w, _ = frame.shape
                
                # Convert normalized coordinates to pixel coordinates
                waist_x = int(waist_point.x * w)
                waist_y = int(waist_point.y * h)
                
                # Draw waist line (horizontal line at waist level)
                cv2.line(frame, (waist_x - 50, waist_y), (waist_x + 50, waist_y), (0, 255, 0), 2)
                cv2.putText(frame, 'Waist', (waist_x + 60, waist_y), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                # Draw hip line
                left_hip = results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_HIP.value]
                right_hip = results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_HIP.value]
                
                left_hip_x, left_hip_y = int(left_hip.x * w), int(left_hip.y * h)
                right_hip_x, right_hip_y = int(right_hip.x * w), int(right_hip.y * h)
                
                cv2.line(frame, (left_hip_x, left_hip_y), (right_hip_x, right_hip_y), (255, 0, 0), 2)
                cv2.putText(frame, 'Hip', (right_hip_x + 10, right_hip_y), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
                
                # Display WHR
                cv2.putText(frame, f'WHR: {whr:.3f}', (50, 50), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                
                # Health category (general guidelines)
                if whr < 0.8:
                    category = "Low Risk"
                    color = (0, 255, 0)
                elif whr < 0.85:
                    category = "Moderate Risk"
                    color = (0, 255, 255)
                else:
                    category = "High Risk"
                    color = (0, 0, 255)
                
                cv2.putText(frame, f'Category: {category}', (50, 90), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                
                return frame, whr
        
        return frame, None
    
    def process_video(self, video_path=0):
        """Process video stream (0 for webcam, or path to video file)"""
        cap = cv2.VideoCapture(video_path)
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            frame, whr = self.process_frame(frame)
            
            # Instructions
            cv2.putText(frame, 'Stand sideways to camera for best results', (50, frame.shape[0] - 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
            cv2.imshow('Waist-Hip Ratio Calculator', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
    
    def process_image(self, image_path):
        """Process a single image"""
        frame = cv2.imread(image_path)
        if frame is None:
            print(f"Could not load image: {image_path}")
            return
        
        frame, whr = self.process_frame(frame)
        
        if whr:
            print(f"Calculated Waist-Hip Ratio: {whr:.3f}")
        else:
            print("No person detected in the image")
        
        cv2.imshow('Waist-Hip Ratio', frame)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

# Usage example
if __name__ == "__main__":
    calculator = WaistHipRatioCalculator()
    
    # For webcam (make sure to stand sideways)
    print("Starting webcam... Press 'q' to quit")
    print("Stand sideways to the camera for best results")
    calculator.process_video(0)
    
    # For image file (uncomment to use)
    # calculator.process_image('path_to_your_image.jpg')
    
    # For video file (uncomment to use)
    # calculator.process_video('path_to_your_video.mp4')
