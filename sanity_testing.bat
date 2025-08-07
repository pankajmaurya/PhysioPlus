@echo off
echo Sanity Testing for Bridging Exercise...

REM Run with debug and save_video flags
python physiocore/bridging.py --debug --video "physiocore/testing/bridging.mp4"

pause