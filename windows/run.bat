@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0\.."

echo.
echo ====================================
echo   Generateur CAR - WinDiag
echo ====================================
echo.

REM Utiliser le Python Launcher (py) pour forcer Python 3.12+
set PYTHON=py -3.12
%PYTHON% --version >nul 2>&1
if errorlevel 1 (
  REM Essayer py -3 (derniere version 3.x disponible)
  set PYTHON=py -3
  %PYTHON% --version >nul 2>&1
  if errorlevel 1 (
    REM Fallback sur python
    set PYTHON=python
    %PYTHON% --version >nul 2>&1
    if errorlevel 1 (
      echo ERREUR: Python introuvable.
      echo.
      echo Installez Python 3.12 depuis https://www.python.org/downloads/
      echo Cochez "Add Python to PATH" pendant l'installation.
      pause
      exit /b 1
    )
  )
)

REM Verifier que la version est >= 3.8
%PYTHON% -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>&1
if errorlevel 1 (
  echo ERREUR: Python trop ancien detecte.
  %PYTHON% --version
  echo.
  echo Desinstallez Python 3.4 via:
  echo   Panneau de configuration - Programmes - Desinstaller
  echo Puis relancez ce fichier.
  pause
  exit /b 1
)

echo Python utilise:
%PYTHON% --version
echo.

REM Mettre a jour pip
%PYTHON% -m pip install --upgrade pip --quiet

REM Installer Flask si absent
%PYTHON% -c "import flask" >nul 2>&1
if errorlevel 1 (
  echo Installation de Flask en cours...
  echo.
  %PYTHON% -m pip install Flask Werkzeug
  if errorlevel 1 (
    echo.
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

%PYTHON% app.py

pause
