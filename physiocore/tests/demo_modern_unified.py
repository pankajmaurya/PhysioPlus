# In demo_unified.py, replace the old argparse with:
from physiocore import create_tracker
from physiocore.lib.modern_flags import get_config

if __name__ == "__main__":
    config = get_config()
    
    if not config.exercise:
        print("Error: exercise name is required (use --exercise or positional argument)")
        sys.exit(1)
    
    print(f"Running exercise: {config.exercise}")
    if config.debug:
        print("Debug mode enabled")
    
    try:
        from physiocore import create_tracker
        tracker = create_tracker(config.exercise)
        tracker.start()
    except ValueError as e:
        print(e)
