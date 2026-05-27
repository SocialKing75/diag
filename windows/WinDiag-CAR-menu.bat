@echo off
setlocal
cd /d "%~dp0\.."

:menu
cls
echo ================================
echo  WinDiag - Outil CAR
echo ================================
echo.
echo 1. Creer un Excel de saisie
echo 2. Generer un CAR depuis Excel
echo 3. Quitter
echo.
set /p CHOICE=Votre choix : 

if "%CHOICE%"=="1" (
  call "windows\01-creer-excel-saisie.bat"
  goto menu
)

if "%CHOICE%"=="2" (
  call "windows\02-generer-car-depuis-excel.bat"
  goto menu
)

if "%CHOICE%"=="3" exit /b 0

echo Choix invalide.
pause
goto menu
