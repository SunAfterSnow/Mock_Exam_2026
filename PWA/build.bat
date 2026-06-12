@echo off
REM ============================================================
REM Build Railway Exam APK (Android App)
REM Requires: Android Studio with Android SDK
REM ============================================================
echo.
echo [1/3] Copying web assets to www/...
if exist www\ rmdir /s /q www\
mkdir www
xcopy index.html www\ /y >nul
xcopy manifest.json www\ /y >nul
xcopy sw.js www\ /y >nul
xcopy data www\data\ /e /y >nul
xcopy static www\static\ /e /y >nul
echo   Done.

echo [2/3] Syncing Capacitor...
call npx cap sync android
echo   Done.

echo [3/3] Building APK...
cd android
call gradlew assembleDebug
cd ..

echo.
echo ============================================
echo APK built successfully!
echo Output: android\app\build\outputs\apk\debug\app-debug.apk
echo ============================================
pause
