import mediapipe as mp
from mediapipe.python.solutions.drawing_utils import DrawingSpec

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