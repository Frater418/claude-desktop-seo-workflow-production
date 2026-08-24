@echo off
setlocal
cd /d "%~dp0"
python scripts\start_operator_console.py %*
if errorlevel 1 (
  echo.
  echo Heartweb Operator Console konnte nicht gestartet werden.
  pause
)
