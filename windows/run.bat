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
  echo ERREUR: Python n'est pas installe ou pas dans le PATH.
  echo.
  echo 1. Allez sur https://www.python.org/downloads/
  echo 2. Telechargez Python 3.12 ou plus recent
  echo 3. IMPORTANT: Cochez "Add Python to PATH" pendant l'installation
  echo 4. Relancez ce fichier
  echo.
  pause
  exit /b 1
)

REM Verifier que la version est >= 3.8
python -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>&1
if errorlevel 1 (
  echo ERREUR: Votre Python est trop ancien !
  echo.
  python --version
  echo.
  echo Flask necessite Python 3.8 minimum.
  echo.
  echo SOLUTION:
  echo 1. Allez sur https://www.python.org/downloads/
  echo 2. Telechargez Python 3.12
  echo 3. Pendant l'installation, cochez "Add Python to PATH"
  echo 4. Redemarrez l'ordinateur
  echo 5. Relancez ce fichier
  echo.
  pause
  exit /b 1
)

echo Python detecte:
python --version
echo.

REM Mettre a jour pip
python -m pip install --upgrade pip --quiet

REM Installer Flask si absent
python -c "import flask" >nul 2>&1
if errorlevel 1 (
  echo Installation de Flask en cours...
  echo Cela peut prendre quelques minutes la premiere fois.
  echo.
  python -m pip install Flask Werkzeug
  if errorlevel 1 (
    echo.
    echo ERREUR lors de l'installation de Flask.
    echo Essayez manuellement: python -m pip install Flask Werkzeug
    echo.
    pause
    exit /b 1
  )
  echo.
  echo Flask installe avec succes !
  echo.
)

echo Demarrage de l'application...
echo Le navigateur va s'ouvrir dans quelques secondes.
echo.
echo Pour arreter: appuyer sur Ctrl+C dans cette fenetre.
echo.

ping -n 3 127.0.0.1 >nul
start "" "http://127.0.0.1:5000"

python app.py

pause
