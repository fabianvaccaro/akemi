@echo off
rem Bootstrap an Akemi graph for an existing codebase.
rem Thin wrapper - delegates to Python for all heavy lifting.
setlocal
set "AKEMI_DIR=%~dp0.."
set "VENV_DIR=%AKEMI_DIR%\.venv"
set "PYTHON=%VENV_DIR%\Scripts\python.exe"

if not exist "%PYTHON%" (
  echo Setting up Akemi Python environment...
  where python >nul 2>nul && python -m venv "%VENV_DIR%" || py -3 -m venv "%VENV_DIR%"
  if not exist "%PYTHON%" (
    echo ERROR: could not create Python virtual environment ^(need Python ^>= 3.10^) 1>&2
    exit /b 1
  )
  "%PYTHON%" -m pip install --quiet --upgrade pip
  "%PYTHON%" -m pip install --quiet "%AKEMI_DIR%\python"
)

"%PYTHON%" -m akemi bootstrap %*
exit /b %errorlevel%
