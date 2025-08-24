import sys
import time
from physiocore.tracker import create_tracker, _TRACKERS

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

def run_exercise_sequence():
    """
    Runs a sequence of exercises, 10 repetitions each.
    """
    exercise_list = list(_TRACKERS.keys())
    print(f"Starting exercise sequence: {exercise_list}")

    for i, exercise in enumerate(exercise_list):
        print(f"--- Starting exercise: {exercise} ---")
        try:
            tracker = create_tracker(exercise, reps=10)
            tracker.start()
            print(f"--- Completed exercise: {exercise} ---")
            
            # Allow time for session complete sound to finish before moving to next exercise
            # Only add delay between exercises, not after the last one
            if i < len(exercise_list) - 1:
                print("Waiting for completion sound to finish...")
                wait_for_sound_completion(max_wait_time=5.0)
                print("Proceeding to next exercise...")
                
        except ValueError as e:
            print(f"Error creating tracker for {exercise}: {e}")
            continue
        except Exception as e:
            print(f"An error occurred during {exercise}: {e}")
            continue

    print("Exercise sequence finished.")

if __name__ == "__main__":
    run_exercise_sequence()
