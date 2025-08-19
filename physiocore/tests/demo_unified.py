import argparse
from physiocore import create_tracker

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a physiotherapy exercise tracker.")
    parser.add_argument("--exercise", "-e", type=str, required=True, help="The name of the exercise to track.")
    #parser.add_argument("exercise", type=str, help="The name of the exercise to track.")
    args = parser.parse_args()

    try:
        tracker = create_tracker(args.exercise)
        tracker.start()
    except ValueError as e:
        print(e)
