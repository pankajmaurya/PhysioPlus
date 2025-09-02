import mediapipe as mp
from mediapipe.python.solutions.drawing_utils import DrawingSpec
import cv2
from dataclasses import dataclass
from typing import Optional, Dict, Any

# Drawing Specifications (Modify these parameters dynamically)
# Moved some of this code out of the while loop - it does not need to run every iteration
landmark_color = (203, 255, 255)  # Color for landmarks (BGR) == cIrcles
connection_color = (240, 203, 58)  # Color for connections (BGR) == Lines
landmark_thickness = 4
connection_thickness = 4
landmark_radius = 4
connection_radius = 0  # Not used for connections

# Live Demo settings
# landmark_color = (203, 255, 255)  # Color for landmarks (BGR) == circles
# connection_color = (240, 203, 58)  # Color for connections (BGR) == lines
# landmark_thickness = 5
# connection_thickness = 10
# landmark_radius = 10
# connection_radius = 0  # Not used for connections

# Initialize Mediapipe Pose and Drawing utilities
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

def pause_loop():
    while True:
        key = cv2.waitKey(0) & 0xFF
        if key == ord("r"):
            return False
        elif key == ord("q"):
            return True

# Set excluded landmarks
default_excluded_landmarks = [0,1,2,3,4,5,6,7,8,9,10,17,18,19,20,21,22]

def get_default_drawing_specs(render_mode):
    if render_mode == 'all':
        return get_drawing_specs(landmark_color, connection_color, 
                                 landmark_thickness, connection_thickness, landmark_radius, connection_radius, [])
    else:
        return get_drawing_specs(landmark_color, connection_color, 
                                 landmark_thickness, connection_thickness, landmark_radius, connection_radius, 
                                 default_excluded_landmarks)
    

# Function to create drawing specs
def get_drawing_specs(landmark_color, connection_color, landmark_thickness, connection_thickness, landmark_radius, connection_radius, excluded_landmarks=None):
    """Return custom drawing specifications."""
    custom_style = mp_drawing_styles.get_default_pose_landmarks_style()
    #print(custom_style)
    custom_connections = list(mp_pose.POSE_CONNECTIONS)
    for landmark in custom_style.keys():
        if landmark in excluded_landmarks:
            custom_style[landmark] = DrawingSpec(color=(255,255,255),circle_radius=0, thickness=None)
            custom_connections = [connection_tuple for connection_tuple in custom_connections 
                            if landmark.value not in connection_tuple]
        else:
            custom_style[landmark] = DrawingSpec(color=landmark_color, thickness=landmark_thickness, circle_radius=landmark_radius)
  
    '''landmark_spec = mp_drawing.DrawingSpec(
        color=landmark_color, thickness=landmark_thickness, circle_radius=landmark_radius
    )'''
    connection_spec = mp_drawing.DrawingSpec(
        color=connection_color, thickness=connection_thickness, circle_radius=connection_radius
    )
    return custom_connections, custom_style, connection_spec


@dataclass
class ExerciseState:
    """Data class to hold exercise state information for rendering."""
    count: int = 0
    debug: bool = False
    render_all: bool = False
    exercise_name: str = "Exercise"
    debug_info: Optional[Dict[str, Any]] = None
    pose_landmarks: Optional[Any] = None
    display: bool = True


class ExerciseInfoRenderer:
    """Shared renderer for exercise information and pose landmarks."""
    
    def __init__(self):
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_pose = mp.solutions.pose
    
    def draw_exercise_info(self, frame, exercise_state: ExerciseState):
        """Draw exercise information on the frame.
        
        Args:
            frame: OpenCV frame to draw on
            exercise_state: ExerciseState object containing all the exercise information
        """
        # Always draw count
        cv2.putText(
            frame, 
            f'Count: {exercise_state.count}', 
            (10, 50), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            1, 
            (255, 0, 0), 
            2
        )
        
        # Draw debug information if enabled
        if exercise_state.debug and exercise_state.debug_info:
            y_offset = 80
            for key, value in exercise_state.debug_info.items():
                # Format the text based on value type
                if isinstance(value, float):
                    text = f'{key}: {value:.2f}'
                elif isinstance(value, tuple) and len(value) == 2 and all(isinstance(v, float) for v in value):
                    text = f'{key}: {value[0]:.2f}, {value[1]:.2f}'
                else:
                    text = f'{key}: {value}'
                
                # Use different colors for different types of information
                color = self._get_debug_color(key)
                cv2.putText(
                    frame, 
                    text, 
                    (10, y_offset), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.7, 
                    color, 
                    2
                )
                y_offset += 30
    
    def draw_pose_landmarks(self, frame, exercise_state: ExerciseState):
        """Draw pose landmarks on the frame.
        
        Args:
            frame: OpenCV frame to draw on
            exercise_state: ExerciseState object containing pose landmarks and render settings
        """
        if exercise_state.pose_landmarks is None:
            return
            
        # Get drawing specifications
        if exercise_state.render_all:
            custom_connections, custom_style, connection_spec = get_default_drawing_specs('all')
        else:
            custom_connections, custom_style, connection_spec = get_default_drawing_specs('')
        
        # Draw landmarks
        self.mp_drawing.draw_landmarks(
            frame, 
            exercise_state.pose_landmarks,
            connections=custom_connections,
            connection_drawing_spec=connection_spec,
            landmark_drawing_spec=custom_style
        )
    
    def show_frame(self, frame, exercise_state: ExerciseState):
        """Display the frame with exercise name as window title.
        
        Args:
            frame: OpenCV frame to display
            exercise_state: ExerciseState object containing display settings
        """
        if exercise_state.display:
            window_name = f'{exercise_state.exercise_name} Exercise'
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
            cv2.imshow(window_name, frame)
    
    def render_complete_frame(self, frame, exercise_state: ExerciseState):
        """Complete rendering pipeline: draw info, landmarks, and optionally show frame.
        
        Args:
            frame: OpenCV frame to render on
            exercise_state: ExerciseState object containing all rendering information
        """
        self.draw_exercise_info(frame, exercise_state)
        self.draw_pose_landmarks(frame, exercise_state)
        self.show_frame(frame, exercise_state)
    
    def _get_debug_color(self, key: str) -> tuple:
        """Get appropriate color for debug information based on key name."""
        key_lower = key.lower()
        if 'angle' in key_lower:
            return (0, 255, 255)  # Yellow for angles
        elif any(word in key_lower for word in ['pose', 'lying', 'ground', 'orientation']):
            return (0, 255, 0)  # Green for pose states
        elif any(word in key_lower for word in ['close', 'near', 'floored']):
            return (255, 255, 0)  # Cyan for proximity states
        else:
            return (0, 255, 0)  # Default green
