from threading import Thread
import cv2
from .platform_utils import save_video_codec
from .sound_utils import play_count_sound, play_session_complete_sound, play_session_complete_sound_blocking, play_welcome_sound_blocking

import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"

import pygame

# Legacy pygame initialization for backward compatibility
try:
    pygame.mixer.init()
    sound_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds", "short-sample.wav")
    pygame.mixer.music.load(sound_path)
except pygame.error:
    print("Could not initialize pygame mixer. Sound will be disabled.")
    # Set sound_path to None or a dummy value if the rest of the code depends on it
    sound_path = None
setFinished = False

def create_output_files(cap, save_video):
    frame_width = int(cap.get(3))
    frame_height = int(cap.get(4))

    input_fps = int(cap.get(cv2.CAP_PROP_FPS))
    # If webcam returns 0 fps, default to 30
    if input_fps <= 0:
        input_fps = 30


    # Split filename and extension
    base_name, extension = os.path.splitext(save_video)
    
    # Create output paths with suffixes
    video_path = f"{base_name}_raw{extension}"
    debug_video_path = f"{base_name}_debug{extension}"

     # Define the codec and create VideoWriter object.The output is stored in 'outpy.avi' file.
    output = cv2.VideoWriter(video_path, save_video_codec, input_fps, (frame_width,frame_height))
    output_with_info = cv2.VideoWriter(debug_video_path, save_video_codec, input_fps, (frame_width,frame_height))

    return output, output_with_info

def release_files(output, output_with_info):
    # Release the video capture and writer objects
    output.release()
    output_with_info.release()

def announceForCount(count, language="english", enabled=True):
    """
    Enhanced announceForCount with new sound system integration.
    Maintains backward compatibility while supporting new features.
    """
    # Use new sound system if available
    try:
        play_count_sound(count, language=language, enabled=enabled)
    except Exception as e:
        print(f"New sound system failed, falling back to legacy: {e}")
        # Fallback to legacy behavior
        if count % 10 == 0:
            Thread(target=announce10).start()
        else:
            Thread(target=announce).start()

def announce():
    global setFinished
    if setFinished:
        sound_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds", "short-sample.wav")
        pygame.mixer.music.load(sound_path)
        setFinished = False 
    try:
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pass

    except Exception as e:
        print(f"Error playing sound: {e}")

def announce10():
    """
    Legacy function for 10-count milestone.
    Maintained for backward compatibility.
    """
    global setFinished
    sound_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds", "set-complete.wav")
    pygame.mixer.music.load(sound_path)
    setFinished = True
    try:
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pass

    except Exception as e:
        print(f"Error playing sound: {e}")

# New convenience functions using the enhanced sound system
def play_exercise_start_sound(exercise_type, language="english", enabled=True):
    """
    Play exercise-specific start sound.
    
    Args:
        exercise_type: Type of exercise (ankle_toe, bridging, cobra, prone_slr, slr)
        language: Language preference (english/indian)
        enabled: Whether sound is enabled
    """
    try:
        from .sound_utils import play_exercise_start_sound as play_start
        play_start(exercise_type, language=language, enabled=enabled)
    except Exception as e:
        print(f"Error playing exercise start sound: {e}")

def play_session_complete_sound(language="english", enabled=True):
    """
    Play session completion sound.
    
    Args:
        language: Language preference (english/indian)
        enabled: Whether sound is enabled
    """
    try:
        from .sound_utils import play_session_complete_sound as play_complete
        play_complete(language=language, enabled=enabled)
    except Exception as e:
        print(f"Error playing session complete sound: {e}")

def play_session_complete_sound_blocking(language="english", enabled=True):
    """
    Play session completion sound (blocking until complete).
    
    Args:
        language: Language preference (english/indian)
        enabled: Whether sound is enabled
    """
    try:
        from .sound_utils import play_session_complete_sound_blocking as play_complete_blocking
        play_complete_blocking(language=language, enabled=enabled)
    except Exception as e:
        print(f"Error playing session complete sound: {e}")

def play_welcome_sound_blocking(language="english", enabled=True):
    """
    Play welcome sound (blocking until complete).
    
    Args:
        language: Language preference (english/indian)
        enabled: Whether sound is enabled
    """
    try:
        from .sound_utils import play_welcome_sound_blocking as play_welcome_blocking
        play_welcome_blocking(language=language, enabled=enabled)
    except Exception as e:
        print(f"Error playing welcome sound: {e}")
