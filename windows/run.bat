@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0\.."

echo.
echo ====================================
echo   Generateur CAR - WinDiag
echo ====================================
echo.

REM Trouver Python 3.8+ - essayer plusieurs commandes
set PYTHON=

REM Essai 1 : py launcher avec versions specifiques
for %%V in (3.13 3.12 3.11 3.10 3.9 3.8) do (
  if "!PYTHON!"=="" (
    py -%%V --version >nul 2>&1
    if not errorlevel 1 set PYTHON=py -%%V
  )
)

REM Essai 2 : py launcher sans version
if "!PYTHON!"=="" (
  py --version >nul 2>&1
  if not errorlevel 1 (
    py -c "import sys; exit(0 if sys.version_info>=(3,8) else 1)" >nul 2>&1
    if not errorlevel 1 set PYTHON=py
  )
)

REM Essai 3 : python3
if "!PYTHON!"=="" (
  python3 --version >nul 2>&1
  if not errorlevel 1 (
    python3 -c "import sys; exit(0 if sys.version_info>=(3,8) else 1)" >nul 2>&1
    if not errorlevel 1 set PYTHON=python3
  )
)

REM Essai 4 : python
if "!PYTHON!"=="" (
  python --version >nul 2>&1
  if not errorlevel 1 (
    python -c "import sys; exit(0 if sys.version_info>=(3,8) else 1)" >nul 2>&1
    if not errorlevel 1 set PYTHON=python
  )
)

REM Aucun Python valide trouve
if "!PYTHON!"=="" (
  echo ERREUR: Python 3.8+ introuvable.
  echo.
  echo Version detectee:
  python --version 2>&1
  py --version 2>&1
  echo.
  echo SOLUTION:
  echo 1. Allez sur https://www.python.org/downloads/
  echo 2. Telechargez Python 3.12
  echo 3. Lancez l installateur
  echo 4. IMPORTANT: cochez "Add Python to PATH"
  echo 5. Redemarrez l ordinateur
  echo 6. Relancez ce fichier
  pause
  exit /b 1
)

echo Python utilise: & !PYTHON! --version
echo.

REM Supprimer l ancien venv si cree avec Python 3.4
if exist "venv\Scripts\python.exe" (
  venv\Scripts\python.exe -c "import sys; exit(0 if sys.version_info>=(3,8) else 1)" >nul 2>&1
  if errorlevel 1 (
    echo Suppression ancien environnement...
    rmdir /s /q venv
  )
)

REM Creer le venv
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

REM Utiliser DIRECTEMENT python.exe du venv
set VP=venv\Scripts\python.exe

REM Mettre a jour pip
echo Mise a jour pip...
%VP% -m pip install --upgrade pip setuptools wheel --quiet

REM Installer Flask
%VP% -c "import flask" >nul 2>&1
if errorlevel 1 (
  echo Installation de Flask...
  %VP% -m pip install Flask Werkzeug
  if errorlevel 1 (
    echo ERREUR installation Flask.
    pause
    exit /b 1
  )
  echo Flask installe !
  echo.
)

echo Demarrage...
echo Navigateur: http://127.0.0.1:5000
echo Ctrl+C pour arreter.
echo.

ping -n 3 127.0.0.1 >nul
start "" "http://127.0.0.1:5000"
%VP% app.py

pause
