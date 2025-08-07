@echo off
echo Starting Bridging Exercise...

REM Get current date and time for filename
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set timestamp=%datetime:~0,8%_%datetime:~8,6%

REM Create videos directory if it doesn't exist
if not exist "videos" mkdir "videos"

REM Run with debug and save_video flags
python physiocore/bridging.py --debug --save_video "videos/bridging_%timestamp%.mp4"

echo Exercise video saved as: bridging_%timestamp%.mp4