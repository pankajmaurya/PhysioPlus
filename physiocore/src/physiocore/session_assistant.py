import sys
import time
from physiocore.tracker import create_tracker, _TRACKERS
from physiocore.lib.voice_utils import play_welcome_sound_blocking, play_exercise_start_sound, play_set_complete_sound_blocking, play_session_complete_sound_blocking
from physiocore.lib.modern_flags import parse_config
from physiocore.lib.exercise_lib import ExerciseType

# Try to import pygame to check if sound is playing
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

def wait_for_sound_completion(max_wait_time=5.0):
    """
    Wait for any currently playing sound to complete.
    
    Args:
        max_wait_time: Maximum time to wait in seconds
    """
    if PYGAME_AVAILABLE:
        # Check if pygame mixer is busy (playing sound)
        wait_time = 0
        while pygame.mixer.music.get_busy() and wait_time < max_wait_time:
            time.sleep(0.1)
            wait_time += 0.1
        
        # Add small buffer after sound stops
        if wait_time > 0:
            time.sleep(0.2)
    else:
        # Fallback: fixed delay if pygame not available
        time.sleep(3.0)

def do_session():
    """
    Runs a sequence of exercises.
    """
    # Get sound configuration from command line flags
    config = parse_config()
    voice_mode = config.voice_mode
    voice_enabled = config.voice_enabled
    
    # exercise_list = sorted(list(_TRACKERS.keys()))
    exercise_list = [ExerciseType.ANKLE_TOE.value, ExerciseType.SLR.value]
    
    # Play welcome sound at the beginning of the sequence
    print(f"🎵 Welcome to PhysioPlus Exercise Sequence! (voice_mode: {voice_mode}, (voice_enabled: {voice_enabled}))")
    try:
        play_welcome_sound_blocking()
        print("Starting exercise sequence...")
    except Exception as e:
        print(f"Welcome sound error: {e}")
        print("Starting exercise sequence...")
    
    print(f"Exercise sequence: {exercise_list}")

    for i, exercise in enumerate(exercise_list):
        print(f"--- Starting exercise: {exercise} ---")
        try:
            tracker = create_tracker(exercise)

            play_exercise_start_sound(exercise)

            tracker.start()
            print(f"--- Completed exercise: {exercise} ---")
            
            print("Waiting for completion sound to finish...")
            wait_for_sound_completion(max_wait_time=15.0)

            # Allow time for session complete sound to finish before moving to next exercise
            # Only add delay between exercises, not after the last one
            if i < len(exercise_list) - 1:
                print("Taking a 5-second break before next exercise...")
                
                play_set_complete_sound_blocking()
                time.sleep(5.0)
                print("Proceeding to next exercise...")
                
        except ValueError as e:
            print(f"Error creating tracker for {exercise}: {e}")
            continue
        except Exception as e:
            print(f"An error occurred during {exercise}: {e}")
            continue

    play_session_complete_sound_blocking()
    print("Exercise sequence finished.")

if __name__ == "__main__":
    do_session()