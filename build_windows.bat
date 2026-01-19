@echo off
REM ========================================
REM Quiz Tool - Windows EXE Builder
REM ========================================
echo.
echo ========================================
echo    Quiz Tool - Windows EXE Builder
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

echo [1/4] Creating virtual environment...
if not exist "venv_build" (
    python -m venv venv_build
)

echo [2/4] Activating environment and installing dependencies...
call venv_build\Scripts\activate.bat
pip install -q -r requirements-build.txt

echo [3/4] Building executable...
pyinstaller --clean --noconfirm quiz_tool.spec

echo [4/4] Copying quizzes folder to dist...
xcopy /E /I /Y quizzes dist\quizzes >nul 2>&1

echo.
echo ========================================
echo    BUILD COMPLETE!
echo ========================================
echo.
echo Your executable is ready at:
echo    dist\QuizTool.exe
echo.
echo To distribute:
echo    1. Copy dist\QuizTool.exe
echo    2. Copy dist\quizzes folder (place next to exe)
echo.
echo Users can add/edit JSON files in quizzes folder.
echo ========================================
echo.
pause
