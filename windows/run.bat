@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0\.."

echo.
echo ====================================
echo   Generateur CAR - WinDiag
echo ====================================
echo.

REM Trouver Python 3.8+ via le Launcher Windows
set PYTHON=
for %%V in (3.13 3.12 3.11 3.10 3.9 3.8) do (
  if "!PYTHON!"=="" (
    py -%%V --version >nul 2>&1
    if not errorlevel 1 (
      set PYTHON=py -%%V
      echo Python %%V detecte.
    )
  )
)

if "!PYTHON!"=="" (
  echo ERREUR: Python 3.8+ introuvable.
  echo.
  echo Installez Python 3.12 depuis https://www.python.org/downloads/
  echo Cochez "Add Python to PATH" pendant l installation.
  pause
  exit /b 1
)

echo.

REM Supprimer l ancien venv si cree avec Python 3.4
if exist "venv\Scripts\python.exe" (
  venv\Scripts\python.exe -c "import sys; exit(0 if sys.version_info >= (3,8) else 1)" >nul 2>&1
  if errorlevel 1 (
    echo Ancien environnement detecte, suppression...
    rmdir /s /q venv
  )
)

REM Creer le venv avec le bon Python
if not exist "venv\Scripts\python.exe" (
  echo Creation de l environnement virtuel...
  !PYTHON! -m venv venv
  if errorlevel 1 (
    echo ERREUR: Impossible de creer le venv.
    pause
    exit /b 1
  )
  echo OK.
  echo.
)

REM Utiliser DIRECTEMENT le python.exe du venv - sans passer par le PATH
set VENV_PYTHON=venv\Scripts\python.exe
set VENV_PIP=venv\Scripts\python.exe -m pip

REM Mettre a jour pip et setuptools via chemin direct
echo Mise a jour de pip...
%VENV_PYTHON% -m pip install --upgrade pip setuptools wheel --quiet
echo.

REM Installer Flask via chemin direct
%VENV_PYTHON% -c "import flask" >nul 2>&1
if errorlevel 1 (
  echo Installation de Flask...
  %VENV_PYTHON% -m pip install Flask Werkzeug
  if errorlevel 1 (
    echo ERREUR lors de l installation de Flask.
    pause
    exit /b 1
  )
  echo Flask installe !
  echo.
)

echo Demarrage de l application...
echo Le navigateur va s ouvrir dans quelques secondes.
echo Pour arreter: Ctrl+C dans cette fenetre.
echo.

ping -n 3 127.0.0.1 >nul
start "" "http://127.0.0.1:5000"

REM Lancer l app avec le python du venv directement
%VENV_PYTHON% app.py

pause
