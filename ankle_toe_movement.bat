@echo off
echo Starting Ankle Toe Movement Exercise Application...

REM Get current date and time for filename
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set timestamp=%datetime:~0,8%_%datetime:~8,6%

REM Create videos directory if it doesn't exist
if not exist "videos" mkdir "videos"

REM Run with debug and save_video flags
python physiocore/ankle_toe_movement.py --debug --save_video "videos/ankle_toe_movement_%timestamp%.mp4"

echo Exercise video saved as: ankle_toe_movement_%timestamp%.mp4