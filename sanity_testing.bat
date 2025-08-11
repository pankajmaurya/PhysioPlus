@echo off
echo Sanity Testing for Bridging Exercise...

REM Run with debug and save_video flags
python "physiocore\src\physiocore\bridging.py" --debug --video "physiocore\tests\bridging.mp4"

pause
