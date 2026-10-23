@echo off
REM Windows helper for running from source (developers). End users should use Setup.exe.
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\pythonw.exe" (
  start "" ".venv\Scripts\pythonw.exe" listener.py
  exit /b 0
)

where pythonw >nul 2>&1
if %ERRORLEVEL%==0 (
  start "" pythonw listener.py
  exit /b 0
)

echo bidi-popup: Python not found. Create a venv first:
echo   python -m venv .venv
echo   .venv\Scripts\pip install -r requirements.txt
exit /b 1
