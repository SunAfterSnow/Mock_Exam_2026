@echo off
chcp 65001 >nul
echo ============================================
echo   Railway Exam - Build Script
echo ============================================
echo.

REM Check if pyinstaller is installed
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller not found. Installing dependencies...
    pip install -r requirements.txt
)

echo [1/2] Cleaning old builds...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "*.spec" del /q "*.spec" 2>nul

echo [2/2] Building RailwayExam.exe...
pyinstaller --onefile --noconsole ^
  --add-data "templates;templates" ^
  --add-data "data;data" ^
  --add-data "static;static" ^
  --icon crsc.ico ^
  --hidden-import flask ^
  --hidden-import jinja2.ext ^
  --hidden-import waitress ^
  --hidden-import flask_cors ^
  --name "RailwayExam" ^
  app.py

if %errorlevel% equ 0 (
    echo.
    echo ============================================
    echo   BUILD SUCCESSFUL!
    echo   Output: dist\RailwayExam.exe
    echo ============================================
) else (
    echo.
    echo ============================================
    echo   BUILD FAILED. Check errors above.
    echo ============================================
)

pause
