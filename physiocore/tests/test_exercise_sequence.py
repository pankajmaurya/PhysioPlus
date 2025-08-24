import sys
from physiocore.tracker import create_tracker, _TRACKERS

def run_exercise_sequence():
    """
    Runs a sequence of exercises, 10 repetitions each.
    """
    exercise_list = list(_TRACKERS.keys())
    print(f"Starting exercise sequence: {exercise_list}")

    for exercise in exercise_list:
        print(f"--- Starting exercise: {exercise} ---")
        try:
            tracker = create_tracker(exercise, reps=10)
            tracker.start()
            print(f"--- Completed exercise: {exercise} ---")
        except ValueError as e:
            print(f"Error creating tracker for {exercise}: {e}")
            continue
        except Exception as e:
            print(f"An error occurred during {exercise}: {e}")
            continue

    print("Exercise sequence finished.")

if __name__ == "__main__":
    run_exercise_sequence()
