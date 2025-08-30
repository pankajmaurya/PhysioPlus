"""
Sound system for PhysioPlus exercise tracking.
Provides audio feedback with multi-language support.
"""

import os
import threading
from typing import Optional, Dict, List
from enum import Enum

# Hide pygame initialization message
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("pygame not available, sound system disabled")

try:
    import playsound
    PLAYSOUND_AVAILABLE = True
except ImportError:
    PLAYSOUND_AVAILABLE = False

class SoundEvent(Enum):
    """Types of sound events for exercise tracking"""
    EXERCISE_START = "start"
    COUNT_INCREMENT = "count"
    MILESTONE_5 = "milestone_5"
    MILESTONE_10 = "milestone_10"
    ENCOURAGEMENT_1 = "encourage_1"
    ENCOURAGEMENT_2 = "encourage_2"
    ENCOURAGEMENT_3 = "encourage_3"
    SESSION_COMPLETE = "complete"
    WELCOME = "welcome"

class ExerciseType(Enum):
    """Supported exercise types"""
    ANKLE_TOE = "ankle_toe"
    BRIDGING = "bridging"
    COBRA = "cobra"
    PRONE_SLR = "prone_slr"
    SLR = "slr"

class SoundManager:
    """
    Manages audio feedback for exercise tracking with multi-language support.
    
    Features:
    - English and Indian language variants
    - Exercise-specific start sounds
    - Progress milestone sounds
    - Encouragement sounds
    - Thread-safe audio playback
    """
    
    def __init__(self, language: str = "english", enabled: bool = True):
        """
        Initialize the sound manager.
        
        Args:
            language: "english" or "indian"
            enabled: Whether sound is enabled
        """
        self.language = language.lower()
        self.enabled = enabled and (PYGAME_AVAILABLE or PLAYSOUND_AVAILABLE)
        self.sounds_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds")
        self._sound_mapping = self._create_sound_mapping()
        self._encouragement_counter = 0
        
        if self.enabled and not os.path.exists(self.sounds_dir):
            print(f"Warning: Sounds directory not found at {self.sounds_dir}")
            self.enabled = False
    
    def _create_sound_mapping(self) -> Dict[str, Dict[str, str]]:
        """Create mapping of exercise types and events to sound files"""
        
        # Exercise-specific start sounds
        exercise_start_sounds = {
            "english": {
                ExerciseType.ANKLE_TOE.value: "DoAnkleToeNow.wav",
                ExerciseType.BRIDGING.value: "DoBridgingPoseNow.wav", 
                ExerciseType.COBRA.value: "DoCobraPoseNow.wav",
                ExerciseType.PRONE_SLR.value: "DoProneSLRNow.wav",
                ExerciseType.SLR.value: "DoSLRNow.wav"
            },
            "indian": {
                ExerciseType.ANKLE_TOE.value: "Indian-DoAnkleToeNow.wav",
                ExerciseType.BRIDGING.value: "Indian-DoBridgingPoseNow.wav",
                ExerciseType.COBRA.value: "Indian-DoCobraPoseNow.wav", 
                ExerciseType.PRONE_SLR.value: "Indian-DoProneSLRNow.wav",
                ExerciseType.SLR.value: "Indian-DoSLRNow.wav"
            }
        }
        
        # Common sounds (not exercise-specific)
        common_sounds = {
            "english": {
                SoundEvent.COUNT_INCREMENT.value: "short-sample.wav",
                SoundEvent.MILESTONE_5.value: "FiveRepeatsCompleted.wav",
                SoundEvent.MILESTONE_10.value: "set-complete.wav",
                SoundEvent.ENCOURAGEMENT_1.value: "GreatFormKeepItUp.wav",
                SoundEvent.ENCOURAGEMENT_2.value: "NiceWorkThreeMoreToGo.wav",
                SoundEvent.ENCOURAGEMENT_3.value: "PerfectYouAreDoingAmazing.wav",
                SoundEvent.SESSION_COMPLETE.value: "WellDoneTakeQuickRest.wav",
                SoundEvent.WELCOME.value: "Welcome.wav"
            },
            "indian": {
                SoundEvent.COUNT_INCREMENT.value: "short-sample.wav",
                SoundEvent.MILESTONE_5.value: "Indian-FiveRepeatsCompleted.wav",
                SoundEvent.MILESTONE_10.value: "set-complete.wav",  # No Indian variant
                SoundEvent.ENCOURAGEMENT_1.value: "Indian-GreatFormKeepItUp.wav",
                SoundEvent.ENCOURAGEMENT_2.value: "Indian-NiceWorkThreeMoreToGo.wav", 
                SoundEvent.ENCOURAGEMENT_3.value: "Indian-PerfectYouAreDoingAmazing.wav",
                SoundEvent.SESSION_COMPLETE.value: "Indian-WellDoneTakeQuickRest.wav",
                SoundEvent.WELCOME.value: "Indian-welcome.wav"
            }
        }
        
        return {
            "exercise_start": exercise_start_sounds,
            "common": common_sounds
        }
    
    def _get_sound_path(self, sound_file: str) -> Optional[str]:
        """Get full path to a sound file"""
        if not sound_file:
            return None
            
        path = os.path.join(self.sounds_dir, sound_file)
        if os.path.exists(path):
            return path
        else:
            print(f"Warning: Sound file not found: {path}")
            return None
    
    def _play_sound_thread(self, sound_path: str) -> None:
        """Play sound in a separate thread to avoid blocking"""
        try:
            if PYGAME_AVAILABLE:
                pygame.mixer.init()
                pygame.mixer.music.load(sound_path)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    pygame.time.wait(100)
            elif PLAYSOUND_AVAILABLE:
                playsound.playsound(sound_path, block=True)
        except Exception as e:
            print(f"Error playing sound {sound_path}: {e}")
    
    def play_sound(self, sound_path: str) -> None:
        """Play a sound file asynchronously"""
        if not self.enabled or not sound_path:
            return
            
        thread = threading.Thread(target=self._play_sound_thread, args=(sound_path,))
        thread.daemon = True
        thread.start()
    
    def play_sound_blocking(self, sound_path: str) -> None:
        """Play a sound file synchronously (blocking until complete)"""
        if not self.enabled or not sound_path:
            return
        
        self._play_sound_thread(sound_path)
    
    def play_exercise_start(self, exercise_type: ExerciseType) -> None:
        """Play exercise-specific start sound"""
        if not self.enabled:
            return
            
        sound_file = self._sound_mapping["exercise_start"][self.language].get(exercise_type.value)
        if sound_file:
            sound_path = self._get_sound_path(sound_file)
            if sound_path:
                self.play_sound(sound_path)
    
    def play_welcome(self) -> None:
        """Play welcome sound"""
        self._play_common_sound(SoundEvent.WELCOME)
    
    def play_welcome_blocking(self) -> None:
        """Play welcome sound (blocking until complete)"""
        self._play_common_sound_blocking(SoundEvent.WELCOME)
    
    def play_count_sound(self, count: int) -> None:
        """
        Play appropriate sound based on count milestones.
        
        Args:
            count: Current exercise count
        """
        if not self.enabled:
            return
            
        if count % 10 == 0 and count > 0:
            self._play_common_sound(SoundEvent.MILESTONE_10)
        elif count % 5 == 0 and count > 0:
            self._play_common_sound(SoundEvent.MILESTONE_5)
        else:
            self._play_common_sound(SoundEvent.COUNT_INCREMENT)
    
    def play_encouragement(self) -> None:
        """Play rotating encouragement sounds"""
        if not self.enabled:
            return
            
        encouragement_events = [
            SoundEvent.ENCOURAGEMENT_1,
            SoundEvent.ENCOURAGEMENT_2, 
            SoundEvent.ENCOURAGEMENT_3
        ]
        
        event = encouragement_events[self._encouragement_counter % len(encouragement_events)]
        self._encouragement_counter += 1
        self._play_common_sound(event)
    
    def play_session_complete(self) -> None:
        """Play session completion sound"""
        self._play_common_sound(SoundEvent.SESSION_COMPLETE)
    
    def play_session_complete_blocking(self) -> None:
        """Play session completion sound (blocking until complete)"""
        self._play_common_sound_blocking(SoundEvent.SESSION_COMPLETE)
    
    def _play_common_sound(self, event: SoundEvent) -> None:
        """Play a common (non-exercise-specific) sound"""
        sound_file = self._sound_mapping["common"][self.language].get(event.value)
        if sound_file:
            sound_path = self._get_sound_path(sound_file)
            if sound_path:
                self.play_sound(sound_path)
    
    def _play_common_sound_blocking(self, event: SoundEvent) -> None:
        """Play a common (non-exercise-specific) sound (blocking)"""
        sound_file = self._sound_mapping["common"][self.language].get(event.value)
        if sound_file:
            sound_path = self._get_sound_path(sound_file)
            if sound_path:
                self.play_sound_blocking(sound_path)
    
    def set_language(self, language: str) -> None:
        """Change the language for audio feedback"""
        self.language = language.lower()
    
    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable sound"""
        self.enabled = enabled and (PYGAME_AVAILABLE or PLAYSOUND_AVAILABLE)

# Global sound manager instance
_sound_manager: Optional[SoundManager] = None

def get_sound_manager(language: str = "english", enabled: bool = True) -> SoundManager:
    """
    Get the global sound manager instance (singleton pattern).
    
    Args:
        language: Audio language preference
        enabled: Whether sound should be enabled
        
    Returns:
        SoundManager instance
    """
    global _sound_manager
    
    if _sound_manager is None:
        _sound_manager = SoundManager(language=language, enabled=enabled)
    else:
        # Update settings if they've changed
        _sound_manager.set_language(language)
        _sound_manager.set_enabled(enabled)
    
    return _sound_manager

def reset_sound_manager() -> None:
    """Reset the global sound manager (useful for testing)"""
    global _sound_manager
    _sound_manager = None

# Convenience functions for common operations
def play_exercise_start_sound(exercise_type: str, language: str = "english", enabled: bool = True) -> None:
    """Play exercise start sound"""
    try:
        exercise_enum = ExerciseType(exercise_type)
        sound_manager = get_sound_manager(language=language, enabled=enabled)
        sound_manager.play_exercise_start(exercise_enum)
    except ValueError:
        print(f"Warning: Unknown exercise type: {exercise_type}")

def play_count_sound(count: int, language: str = "english", enabled: bool = True) -> None:
    """Play count-based sound"""
    sound_manager = get_sound_manager(language=language, enabled=enabled)
    sound_manager.play_count_sound(count)

def play_session_complete_sound(language: str = "english", enabled: bool = True) -> None:
    """Play session completion sound"""
    sound_manager = get_sound_manager(language=language, enabled=enabled)
    sound_manager.play_session_complete()

def play_session_complete_sound_blocking(language: str = "english", enabled: bool = True) -> None:
    """Play session completion sound (blocking until complete)"""
    sound_manager = get_sound_manager(language=language, enabled=enabled)
    sound_manager.play_session_complete_blocking()

def play_welcome_sound(language: str = "english", enabled: bool = True) -> None:
    """Play welcome sound"""
    sound_manager = get_sound_manager(language=language, enabled=enabled)
    sound_manager.play_welcome()

def play_welcome_sound_blocking(language: str = "english", enabled: bool = True) -> None:
    """Play welcome sound (blocking until complete)"""
    sound_manager = get_sound_manager(language=language, enabled=enabled)
    sound_manager.play_welcome_blocking()

def play_encouragement_sound(language: str = "english", enabled: bool = True) -> None:
    """Play encouragement sound"""
    sound_manager = get_sound_manager(language=language, enabled=enabled)
    sound_manager.play_encouragement()