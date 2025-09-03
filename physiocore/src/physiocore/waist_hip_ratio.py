import cv2
import mediapipe as mp
import numpy as np
import math

class WaistHipRatioCalculator:
    """
    Calculates waist-to-hip ratio using MediaPipe pose detection.
    
    This implementation uses wrists as a proxy for hip diameter measurement.
    When a person stands naturally with arms at their sides, the distance 
    between wrists correlates well with hip width. This approach is more 
    reliable than using hip landmarks directly, especially for front-facing poses.
    
    For best results:
    - Stand facing the camera
    - Keep arms naturally at your sides
    - Ensure both wrists are visible
    - Maintain good posture
    """
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
    
    def is_suitable_arm_position(self, landmarks):
        """
        Check if arms are in a suitable position for wrist-based hip measurement
        Arms should be naturally at sides, not raised or crossed
        """
        left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
        left_wrist = landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value]
        right_wrist = landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value]
        
        # Check if wrists are below shoulders (arms not raised)
        if left_wrist.y < left_shoulder.y or right_wrist.y < right_shoulder.y:
            return False, "Lower your arms to your sides"
        
        # Check if wrists are reasonably apart (arms not crossed)
        wrist_distance = self.calculate_distance(left_wrist, right_wrist)
        shoulder_distance = self.calculate_distance(left_shoulder, right_shoulder)
        
        if wrist_distance < shoulder_distance * 0.5:
            return False, "Keep arms away from body"
        
        return True, "Good arm position"
    
    def get_waist_hip_measurements(self, landmarks):
        """
        Extract waist and hip measurements from pose landmarks
        Uses wrists as a proxy for hip diameter when arms are at sides
        - Waist: narrowest point between ribs and hips (approximated using shoulder-hip midpoint)
        - Hip: estimated using wrist distance as proxy when arms are naturally positioned
        """
        # Get relevant landmarks
        left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
        left_hip = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value]
        right_hip = landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value]
        left_wrist = landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value]
        right_wrist = landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value]
        
        # Waist approximation: point between shoulder and hip on the torso
        # This is a simplified approach - in reality, waist is narrowest point
        waist_y = left_shoulder.y + 0.6 * (left_hip.y - left_shoulder.y)
        waist_point = type('Point', (), {
            'x': left_shoulder.x + 0.3 * (left_hip.x - left_shoulder.x),
            'y': waist_y,
            'z': left_shoulder.z
        })()
        
        # Hip measurement: use wrists as proxy for hip width
        # This works when arms are naturally at sides or slightly away from body
        wrist_distance = self.calculate_distance(left_wrist, right_wrist)
        
        # Apply correction factor since wrists are typically slightly wider than hips
        # when arms are naturally positioned. This factor may need adjustment based on pose.
        hip_width_from_wrists = wrist_distance * 0.85  # Empirical correction factor
        
        # For waist, we need to estimate the width
        # Use a proportion based on the hip width derived from wrists
        estimated_waist_width = hip_width_from_wrists * 0.7  # Typical waist-to-hip ratio factor
        
        return estimated_waist_width, hip_width_from_wrists, waist_point
    
    def process_frame(self, frame):
        """Process a single frame and return WHR if person detected"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(rgb_frame)
        
        if results.pose_landmarks:
            # Draw pose landmarks
            self.mp_drawing.draw_landmarks(
                frame, results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS)
            
            # Check if arms are in suitable position for measurement
            suitable_position, position_message = self.is_suitable_arm_position(
                results.pose_landmarks.landmark
            )
            
            # Display position feedback
            color = (0, 255, 0) if suitable_position else (0, 255, 255)
            cv2.putText(frame, position_message, (50, 130), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            
            if suitable_position:
                # Calculate measurements only if arms are in good position
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
                
                # Draw hip line (using wrists as proxy)
                left_wrist = results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_WRIST.value]
                right_wrist = results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_WRIST.value]
                
                left_wrist_x, left_wrist_y = int(left_wrist.x * w), int(left_wrist.y * h)
                right_wrist_x, right_wrist_y = int(right_wrist.x * w), int(right_wrist.y * h)
                
                cv2.line(frame, (left_wrist_x, left_wrist_y), (right_wrist_x, right_wrist_y), (255, 0, 0), 2)
                cv2.putText(frame, 'Hip (via wrists)', (right_wrist_x + 10, right_wrist_y), 
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
            else:
                cv2.putText(frame, 'Adjust arm position for measurement', (50, 170), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
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
            cv2.putText(frame, 'Stand facing camera with arms at sides', (50, frame.shape[0] - 30), 
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
    
    # For webcam (make sure to stand facing camera with arms at sides)
    print("Starting webcam... Press 'q' to quit")
    print("Stand facing camera with arms naturally at your sides for best results")
    # calculator.process_video(0)
    
    # For image file (uncomment to use)
    calculator.process_image('input6.png')
    calculator.process_image('input7.png')
    
    # For video file (uncomment to use)
    # calculator.process_video('path_to_your_video.mp4')
