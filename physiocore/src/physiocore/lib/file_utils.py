from threading import Thread
import cv2
from .platform_utils import save_video_codec
from .voice_utils import play_count_sound

import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"

import pygame

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

def announceForCount(count):
    play_count_sound(count)

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

    
