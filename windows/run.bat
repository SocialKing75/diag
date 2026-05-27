@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0\.."

echo.
echo ====================================
echo   Generateur CAR - WinDiag
echo ====================================
echo.

REM Trouver Python 3.8+
set PYTHON=
py -3.12 --version >nul 2>&1 && set PYTHON=py -3.12
if "!PYTHON!"=="" py -3.11 --version >nul 2>&1 && set PYTHON=py -3.11
if "!PYTHON!"=="" py -3.10 --version >nul 2>&1 && set PYTHON=py -3.10
if "!PYTHON!"=="" py -3.9  --version >nul 2>&1 && set PYTHON=py -3.9
if "!PYTHON!"=="" py -3.8  --version >nul 2>&1 && set PYTHON=py -3.8
if "!PYTHON!"=="" py -3    --version >nul 2>&1 && set PYTHON=py -3

if "!PYTHON!"=="" (
  echo ERREUR: Python 3.8+ introuvable.
  echo Installez Python 3.12 depuis https://www.python.org/downloads/
  pause
  exit /b 1
)

echo Python utilise: & !PYTHON! --version
echo.

REM Creer l'environnement virtuel si absent
if not exist "venv\Scripts\activate.bat" (
  echo Creation de l'environnement virtuel...
  !PYTHON! -m venv venv
  if errorlevel 1 (
    echo ERREUR: Impossible de creer l'environnement virtuel.
    pause
    exit /b 1
  )
  echo OK.
  echo.
)

REM Activer le venv
call venv\Scripts\activate.bat

REM Mettre a jour pip et setuptools
python -m pip install --upgrade pip setuptools wheel --quiet

REM Installer Flask si absent
python -c "import flask" >nul 2>&1
if errorlevel 1 (
  echo Installation de Flask en cours...
  pip install Flask Werkzeug
  if errorlevel 1 (
    echo ERREUR lors de l'installation.
    pause
    exit /b 1
  )
  echo Flask installe !
  echo.
)

echo Demarrage de l'application...
echo Le navigateur va s'ouvrir dans quelques secondes.
echo Pour arreter: Ctrl+C dans cette fenetre.
echo.

ping -n 3 127.0.0.1 >nul
start "" "http://127.0.0.1:5000"

python app.py

pause
