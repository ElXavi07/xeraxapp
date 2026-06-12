@echo off
setlocal
cd /d "%~dp0.."

where python >nul 2>nul
if errorlevel 1 (
  echo Python 3 is required. Install it from https://www.python.org/downloads/
  pause
  exit /b 1
)

where adb >nul 2>nul
if errorlevel 1 (
  echo Warning: adb was not found on PATH.
)

where fastboot >nul 2>nul
if errorlevel 1 (
  echo Warning: fastboot was not found on PATH.
)

echo Starting Xerax Root companion with flashing enabled.
echo Close this window to stop the companion.
echo.
python agent\xerax_agent.py --enable-flashing

if errorlevel 1 (
  echo.
  echo The companion stopped with an error.
  pause
)
