@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0\.."

echo.
echo ====================================
echo   Generateur CAR - WinDiag
echo ====================================
echo.

REM Verifier si Python est installe
python --version >nul 2>&1
if errorlevel 1 (
  echo ERROR: Python n'est pas installe ou pas dans le PATH.
  echo.
  echo Installez Python 3.8+ depuis https://www.python.org
  echo et selectionnez "Add Python to PATH" pendant l'installation.
  pause
  exit /b 1
)

REM Verifier les dependances
python -c "import flask" >nul 2>&1
if errorlevel 1 (
  echo Installation des dependances...
  python -m pip install -r requirements.txt
  if errorlevel 1 (
    echo Erreur lors de l'installation.
    pause
    exit /b 1
  )
)

echo.
echo Demarrage de l'application...
echo Le navigateur va s'ouvrir automatiquement.
echo.
echo Appuyer sur Ctrl+C pour arreter l'application.
echo.

REM Ouvrir le navigateur
start "" "http://127.0.0.1:5000"

REM Lancer Flask
python app.py

pause
