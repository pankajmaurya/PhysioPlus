@echo off
echo Starting Neck Rotation Exercise...

REM Get current date and time for filename
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set timestamp=%datetime:~0,8%_%datetime:~8,6%

REM Create videos directory if it doesn't exist
if not exist "videos" mkdir "videos"

REM Run with debug and save_video flags
python "physiocore\src\physiocore\neck_rotation.py" --debug --save_video "videos\neck_rotation_%timestamp%.mp4"

echo Exercise video saved as: neck_rotation_%timestamp%.mp4
