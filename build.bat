@echo off
setlocal enabledelayedexpansion

set LOG_FILE=build_log_%date:~-4,4%%date:~-7,2%%date:~-10,2%_%time:~0,2%%time:~3,2%%time:~6,2%.txt
set LOG_FILE=%LOG_FILE: =0%

echo ====================================
echo   Aim Trainer - Build Script
echo ====================================
echo.
echo Log file: %LOG_FILE%
echo.

echo [START] Build started at %date% %time% >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Install Python 3.8+
    echo [ERROR] Python not found! Install Python 3.8+ >> "%LOG_FILE%"
    pause
    exit /b 1
)

python --version >> "%LOG_FILE%" 2>&1
echo Python found >> "%LOG_FILE%"

echo [1/5] Checking virtual environment...
echo [1/5] Checking virtual environment... >> "%LOG_FILE%"
if not exist ".venv" (
    echo [INFO] Creating virtual environment...
    echo [INFO] Creating virtual environment... >> "%LOG_FILE%"
    python -m venv .venv >> "%LOG_FILE%" 2>&1
    if errorlevel 1 (
        echo [ERROR] Failed to create venv
        echo [ERROR] Failed to create venv >> "%LOG_FILE%"
        pause
        exit /b 1
    )
) else (
    echo Virtual environment already exists >> "%LOG_FILE%"
)

echo [2/5] Activating virtual environment...
echo [2/5] Activating virtual environment... >> "%LOG_FILE%"
call .venv\Scripts\activate.bat >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to activate venv
    echo [ERROR] Failed to activate venv >> "%LOG_FILE%"
    pause
    exit /b 1
)
echo Virtual environment activated >> "%LOG_FILE%"

echo [3/5] Installing dependencies...
echo [3/5] Installing dependencies... >> "%LOG_FILE%"
python -m pip install --upgrade pip >> "%LOG_FILE%" 2>&1
pip install -r requirements.txt >> "%LOG_FILE%" 2>&1
pip install pyinstaller >> "%LOG_FILE%" 2>&1
echo Dependencies installed >> "%LOG_FILE%"

echo [4/5] Cleaning old builds...
echo [4/5] Cleaning old builds... >> "%LOG_FILE%"
if exist "build" (
    rmdir /s /q build >> "%LOG_FILE%" 2>&1
    echo Removed build folder >> "%LOG_FILE%"
)
if exist "dist" (
    rmdir /s /q dist >> "%LOG_FILE%" 2>&1
    echo Removed dist folder >> "%LOG_FILE%"
)
if exist "*.spec" (
    del /q *.spec >> "%LOG_FILE%" 2>&1
    echo Removed spec files >> "%LOG_FILE%"
)
echo Cleanup completed >> "%LOG_FILE%"

echo [5/5] Building EXE...
echo [5/5] Building EXE... >> "%LOG_FILE%"
echo PyInstaller command: >> "%LOG_FILE%"
echo pyinstaller --noconfirm --name="AimTrainer" --windowed --onedir ... >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

pyinstaller --noconfirm --name="AimTrainer" --windowed --onedir --icon="assets/icon.ico" --add-data="assets;assets" --add-data="sounds;sounds" --add-data="music;music" --add-data="models;models" --add-data="model_textures;model_textures" --add-data="images;images" --add-data="shader_presets;shader_presets" --add-data="shaders;shaders" --hidden-import="panda3d.core" --hidden-import="direct.showbase.ShowBase" --hidden-import="direct.task.Task" --hidden-import="direct.gui.DirectGui" --hidden-import="direct.interval.IntervalGlobal" --hidden-import="direct.actor.Actor" --hidden-import="imgui_bundle" --hidden-import="imgui_bundle.imgui" --hidden-import="p3dimgui" --hidden-import="p3dimgui.backend" --hidden-import="p3dimgui.shaders" --collect-all="panda3d" --collect-all="imgui_bundle" --collect-all="p3dimgui" main.py >> "%LOG_FILE%" 2>&1

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed!
    echo [ERROR] Build failed at %date% %time% >> "%LOG_FILE%"
    echo Check log file: %LOG_FILE%
    pause
    exit /b 1
)
echo Build completed successfully >> "%LOG_FILE%"

echo.
echo ====================================
echo   Build completed successfully!
echo   Folder: dist\AimTrainer\
echo   Run: dist\AimTrainer\AimTrainer.exe
echo ====================================
echo.
echo [END] Build finished at %date% %time% >> "%LOG_FILE%"
echo Log saved to: %LOG_FILE%
echo.
pause
