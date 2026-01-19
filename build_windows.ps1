# ========================================
# Quiz Tool - Windows EXE Builder (PowerShell)
# ========================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Quiz Tool - Windows EXE Builder" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ from python.org"
    Read-Host "Press Enter to exit"
    exit 1
}

# Create virtual environment
Write-Host "[1/4] Creating virtual environment..." -ForegroundColor Yellow
if (-not (Test-Path "venv_build")) {
    python -m venv venv_build
}

# Activate and install
Write-Host "[2/4] Installing dependencies..." -ForegroundColor Yellow
& .\venv_build\Scripts\Activate.ps1
pip install -q -r requirements-build.txt

# Build
Write-Host "[3/4] Building executable..." -ForegroundColor Yellow
pyinstaller --clean --noconfirm quiz_tool.spec

# Copy quizzes folder
Write-Host "[4/4] Copying quizzes folder..." -ForegroundColor Yellow
Copy-Item "quizzes" -Destination "dist\quizzes" -Recurse -Force

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "   BUILD COMPLETE!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Your executable is ready at:" -ForegroundColor White
Write-Host "   dist\QuizTool.exe" -ForegroundColor Cyan
Write-Host ""
Write-Host "To distribute:" -ForegroundColor White
Write-Host "   1. Copy dist\QuizTool.exe"
Write-Host "   2. Copy dist\quizzes folder (place next to exe)"
Write-Host ""
Write-Host "Users can add/edit JSON files in quizzes folder."
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Read-Host "Press Enter to exit"
