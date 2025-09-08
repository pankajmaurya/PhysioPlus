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
        Extract waist and hip measurements from pose landmarks.
        - Waist: Approximated as the width between points on the torso.
        - Hip: Estimated using wrist distance as a proxy.
        """
        # Get relevant landmarks
        left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
        left_hip = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value]
        right_hip = landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value]
        left_wrist = landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value]
        right_wrist = landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value]

        # Define waist points on both sides of the torso
        waist_y_level = left_shoulder.y + 0.5 * (left_hip.y - left_shoulder.y)
        
        left_waist_point = type('Point', (), {
            'x': (left_shoulder.x + left_hip.x) / 2,
            'y': waist_y_level,
            'z': (left_shoulder.z + left_hip.z) / 2
        })()
        
        right_waist_point = type('Point', (), {
            'x': (right_shoulder.x + right_hip.x) / 2,
            'y': waist_y_level,
            'z': (right_shoulder.z + right_hip.z) / 2
        })()

        # Calculate waist width as the distance between the two waist points
        waist_width = self.calculate_distance(left_waist_point, right_waist_point)

        # Hip measurement: use wrists as proxy for hip width
        wrist_distance = self.calculate_distance(left_wrist, right_wrist)
        
        # Correction factor for hip width from wrists
        hip_width = wrist_distance * 0.9  # Adjusted empirical correction factor

        return waist_width, hip_width, left_waist_point, right_waist_point

    def process_frame(self, frame):
        """Process a single frame and return WHR if person detected"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(rgb_frame)
        
        waist_width, hip_width = 0, 0  # Initialize with default values

        if results.pose_landmarks:
            self.mp_drawing.draw_landmarks(
                frame, results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS)
            
            suitable_position, position_message = self.is_suitable_arm_position(
                results.pose_landmarks.landmark)
            
            color = (0, 255, 0) if suitable_position else (0, 255, 255)
            cv2.putText(frame, position_message, (50, 130), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            
            if suitable_position:
                waist_width, hip_width, l_waist, r_waist = self.get_waist_hip_measurements(
                    results.pose_landmarks.landmark)
                
                # Draw measurement lines
                h, w, _ = frame.shape
                
                # Waist line
                lw_x, lw_y = int(l_waist.x * w), int(l_waist.y * h)
                rw_x, rw_y = int(r_waist.x * w), int(r_waist.y * h)
                cv2.line(frame, (lw_x, lw_y), (rw_x, rw_y), (0, 255, 0), 2)
                cv2.putText(frame, 'Waist', (rw_x + 10, rw_y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                # Hip line (using wrists)
                l_wrist = results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_WRIST.value]
                r_wrist = results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_WRIST.value]
                lw_x, lw_y = int(l_wrist.x * w), int(l_wrist.y * h)
                rw_x, rw_y = int(r_wrist.x * w), int(r_wrist.y * h)
                cv2.line(frame, (lw_x, lw_y), (rw_x, rw_y), (255, 0, 0), 2)
                cv2.putText(frame, 'Hip (via wrists)', (rw_x + 10, rw_y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

            if hip_width > 0:
                whr = waist_width / hip_width
                
                # Display WHR and health category
                cv2.putText(frame, f'WHR: {whr:.3f}', (50, 50), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                
                if whr < 0.85:
                    category, color = "Low Risk", (0, 255, 0)
                elif whr < 0.9:
                    category, color = "Moderate Risk", (0, 255, 255)
                else:
                    category, color = "High Risk", (0, 0, 255)
                
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
            cv2.putText(frame, 'Stand facing camera with arms at sides', (50, frame.shape[0] - 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
            cv2.imshow('Waist-Hip Ratio Calculator', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
    
    def process_image(self, image_path, output_path=None):
        """Process a single image and save the output."""
        frame = cv2.imread(image_path)
        if frame is None:
            print(f"Could not load image: {image_path}")
            return

        processed_frame, whr = self.process_frame(frame)

        if whr:
            print(f"Calculated Waist-Hip Ratio: {whr:.3f}")
        else:
            print("Could not calculate WHR. Check if person is visible and in a suitable pose.")

        if output_path:
            cv2.imwrite(output_path, processed_frame)
            print(f"Saved processed image to {output_path}")
        else:
            # Fallback for environments where display is available
            cv2.imshow('Waist-Hip Ratio', processed_frame)
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
    calculator.process_image('input1.png')
    calculator.process_image('input2.png')
    calculator.process_image('input3.png')
    calculator.process_image('input4.png')
    calculator.process_image('input5.png')
    calculator.process_image('input6.png')
    calculator.process_image('input7.png')
    
    # For video file (uncomment to use)
    # calculator.process_video('path_to_your_video.mp4')
