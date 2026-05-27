@echo off
setlocal
cd /d "%~dp0\.."

echo.
echo Creation d'un Excel de saisie CAR
echo.
set /p TEMPLATE=Chemin du fichier modele .CAR : 
if "%TEMPLATE%"=="" (
  echo Aucun modele indique.
  pause
  exit /b 1
)

set /p OUTPUT=Nom du fichier Excel a creer [exports\saisie-car.xlsx] : 
if "%OUTPUT%"=="" set OUTPUT=exports\saisie-car.xlsx

python car_tool.py excel-template --template "%TEMPLATE%" --output "%OUTPUT%"
if errorlevel 1 (
  echo.
  echo Erreur pendant la creation de l'Excel.
  pause
  exit /b 1
)

echo.
echo Excel cree : %OUTPUT%
echo Ouvrez ce fichier, modifiez la colonne Valeur, puis lancez 02-generer-car-depuis-excel.bat.
pause
