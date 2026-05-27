@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0\.."

echo.
echo ====================================
echo  OCR image vers fichier texte
echo ====================================
echo.

set TESSERACT=
where tesseract >nul 2>&1
if not errorlevel 1 set TESSERACT=tesseract

if "%TESSERACT%"=="" (
  if exist "C:\Program Files\Tesseract-OCR\tesseract.exe" set TESSERACT=C:\Program Files\Tesseract-OCR\tesseract.exe
)

if "%TESSERACT%"=="" (
  if exist "C:\Program Files (x86)\Tesseract-OCR\tesseract.exe" set TESSERACT=C:\Program Files (x86)\Tesseract-OCR\tesseract.exe
)

if "%TESSERACT%"=="" (
  echo ERREUR: Tesseract OCR n'est pas installe.
  echo.
  echo Installation:
  echo 1. Ouvrir cette page:
  echo    https://github.com/UB-Mannheim/tesseract/wiki
  echo 2. Installer Tesseract pour Windows
  echo 3. Relancer ce fichier
  echo.
  pause
  exit /b 1
)

set /p IMAGE=Glisser/deposer l'image ici puis Entrer : 
set IMAGE=%IMAGE:"=%

if "%IMAGE%"=="" (
  echo Aucune image indiquee.
  pause
  exit /b 1
)

if not exist "%IMAGE%" (
  echo Image introuvable:
  echo %IMAGE%
  pause
  exit /b 1
)

set /p OUTPUT=Fichier texte a creer [exports\texte-image.txt] : 
if "%OUTPUT%"=="" set OUTPUT=exports\texte-image.txt
set OUTPUT=%OUTPUT:"=%

if not exist "exports" mkdir exports

set BASE=%OUTPUT%
if /i "%BASE:~-4%"==".txt" set BASE=%BASE:~0,-4%

echo.
echo Lecture OCR en cours...
echo Image : %IMAGE%
echo Sortie: %BASE%.txt
echo.

"%TESSERACT%" "%IMAGE%" "%BASE%" -l fra+eng

if errorlevel 1 (
  echo.
  echo ERREUR pendant la lecture OCR.
  echo Verifiez que l'image est nette et que Tesseract est bien installe avec la langue francaise.
  pause
  exit /b 1
)

echo.
echo Texte extrait:
echo %BASE%.txt
echo.
start "" "%BASE%.txt"
pause
