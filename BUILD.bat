@echo off
echo.
echo =========================================
echo  Clipboard Security Manager : Build
echo =========================================
echo.

REM Step 0: Encode your company Gmail credentials
echo [STEP 0] Encode company credentials first:
echo   python tools\encode_creds.py  sender@gmail.com  YourAppPassword16
echo   Then paste _EA and _AP into core\email_service.py
echo.
pause

python --version >nul 2>&1 || (echo [ERROR] Python not found & pause & exit /b 1)

if not exist venv python -m venv venv
call venv\Scripts\python.exe -m pip install -q -r requirements.txt
call venv\Scripts\python.exe -m pip install -q pyinstaller

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo [STEP 1.5] Clearing Python Caches...
del /s /q *.pyc >nul 2>&1
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

echo [STEP 2] Verifying Assets:
if not exist "Email Templates" (echo [ERROR] Email Templates missing! & pause & exit /b 1)
if not exist "ui" (echo [ERROR] UI assets missing! & pause & exit /b 1)
dir "Email Templates\*.html" /b
echo.

echo [STEP 3] Running PyInstaller...
call venv\Scripts\python.exe -m PyInstaller CSM.spec --noconfirm --clean
if errorlevel 1 (echo [ERROR] Build failed & pause & exit /b 1)

echo [STEP 4] Asset Validation...
REM assets are bundled into the EXE by CSM.spec for One-File mode.
if exist "dist\_internal" (
    echo [INFO] One-Directory mode detected. Syncing assets...
    xcopy "Email Templates\*" "dist\_internal\Email Templates\" /Y /E /I
    xcopy "ui\*.png" "dist\_internal\ui\" /Y /I
) else (
    echo [INFO] One-File mode detected. Assets bundled internally.
)

echo.
echo =========================================
echo  SUCCESS: dist\CSM Setup.exe
echo  Run it to go through the 7-step installer.
echo =========================================
pause
