@echo off
setlocal
cd /d "%~dp0"
set "HEARTWEB_PYTHON=%LOCALAPPDATA%/Heartweb/runtime/Scripts/python.exe"
if not exist "%HEARTWEB_PYTHON%" (
  echo ERROR_OPERATOR_RUNTIME_MISSING: Die lokale Heartweb-Laufzeit fehlt.
  echo Erwartet: %HEARTWEB_PYTHON%
  pause
  exit /b 2
)
"%HEARTWEB_PYTHON%" scripts\start_operator_console.py %*
if errorlevel 1 (
  echo.
  echo Heartweb Operator Console konnte nicht gestartet werden.
  pause
)
