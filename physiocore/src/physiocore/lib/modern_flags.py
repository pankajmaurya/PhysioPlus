"""
Unified argument parsing module using argparse.
"""

import argparse
import sys
from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    """Configuration object containing all parsed flags"""
    debug: bool = False
    video: Optional[str] = None
    render_all: bool = False
    save_video: Optional[str] = None
    lenient_mode: bool = True
    fps: int = 30
    out_fps: int = 30
    exercise: Optional[str] = None
    reps: int = 10
    voice_enabled: bool = True
    voice_mode: str = "hindi"

# Global cache for parsed configuration
_cached_config = None

def _create_parser() -> argparse.ArgumentParser:
    """Create the unified argument parser"""
    parser = argparse.ArgumentParser(
        description="Physiotherapy exercise tracker with configurable flags.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Core flags (common to all original functions)
    parser.add_argument('--debug', action='store_true', 
                       help='Enable debug mode')
    parser.add_argument('--video', type=str, 
                       help='Video file path to process')
    parser.add_argument('--render_all', action='store_true',
                       help='Render all frames')
    parser.add_argument('--save_video', type=str,
                       help='Save processed video to specified path')
    parser.add_argument('--fps', type=int, default=30,
                       help='Input frames per second')
    
    # Lenient mode (with proper boolean parsing)
    parser.add_argument('--lenient_mode', type=str, default='True',
                       choices=['True', 'False', 'true', 'false'],
                       help='Enable lenient mode')
    
    parser.add_argument('--out_fps', type=int, default=30,
                       help='Output frames per second')
        
    # Exercise option (can be used as flag or positional)
    parser.add_argument('--exercise', type=str,
                       help='Name of the exercise to track')

    parser.add_argument('--reps', type=int, default=100,
                       help='repeats per exercise')
    
    parser.add_argument('--voice_enabled', type=str, default='True',
                       choices=['True', 'False', 'true', 'false'],
                       help='Enable or disable sound feedback')

    parser.add_argument('--voice_mode', type=str, default='hindi',
                       choices=['american', 'indian', 'hindi'],
                       help='Voice Mode for audio feedback')

    # Handle unknown positional arguments gracefully (for backward compatibility)
    parser.add_argument('remaining_args', nargs='*',
                       help='Additional positional arguments')
    
    return parser

def parse_config() -> Config:
    """
    Parse command line arguments into a Config object.
    Safe to call multiple times - results are cached.
    """
    global _cached_config
    
    if _cached_config is not None:
        return _cached_config
    
    parser = _create_parser()
    args = parser.parse_args()
    
    # Convert lenient_mode string to boolean
    lenient_mode = args.lenient_mode.lower() == 'true'
    
    # Handle exercise - can come from --exercise flag or first positional arg
    exercise = args.exercise
    if not exercise and args.remaining_args:
        exercise = args.remaining_args[0]  # Use first positional arg as exercise
    
    # Create config object
    config = Config(
        debug=args.debug,
        video=args.video,
        render_all=args.render_all,
        save_video=args.save_video,
        lenient_mode=lenient_mode,
        fps=args.fps,
        out_fps=args.out_fps,
        exercise=exercise,
        reps=args.reps,
        voice_enabled=args.voice_enabled.lower() == 'true',
        voice_mode=args.voice_mode
    )
    
    # Print settings (matching your original format)
    print(f"Settings are --debug {config.debug}, --video {config.video}, "
          f"--render_all {config.render_all}, --save_video {config.save_video}, "
          f"--lenient_mode {config.lenient_mode}, --fps {config.fps}, "
          f"--out_fps {config.out_fps}, --reps {config.reps}, "
          f"--exercise {config.exercise}, --voice_enabled {config.voice_enabled}, "
          f"--voice_mode {config.voice_mode}")
    
    _cached_config = config
    return config

def reset_config():
    """Reset the cached configuration (useful for testing)"""
    global _cached_config
    _cached_config = None

# Modern usage example
def get_config() -> Config:
    """
    Modern way to access configuration.
    Recommended for new code.
    """
    return parse_config()

if __name__ == "__main__":
    # Demo of all approaches
    print("=== Testing new config approach ===")
    config = get_config()
    print(f"Debug: {config.debug}")
    print(f"Video: {config.video}")
    print(f"Exercise: {config.exercise}")
    print(f"FPS: {config.fps}")
    print(f"Out FPS: {config.out_fps}")
    print(f"Repeats: {config.reps}")
            
    print("\n=== Multiple calls test (should use cache) ===")
    config2 = get_config()
    print(f"Same object: {config is config2}")  # Should be True due to caching
