@echo off
setlocal
cd /d "%~dp0\.."

echo.
echo Generation d'un fichier CAR depuis un Excel de saisie
echo.
set /p TEMPLATE=Chemin du fichier modele .CAR : 
if "%TEMPLATE%"=="" (
  echo Aucun modele indique.
  pause
  exit /b 1
)

set /p EXCEL=Chemin du fichier Excel rempli [exports\saisie-car.xlsx] : 
if "%EXCEL%"=="" set EXCEL=exports\saisie-car.xlsx

set /p OUTPUT=Nom du fichier CAR a creer [exports\nouveau-dossier.CAR] : 
if "%OUTPUT%"=="" set OUTPUT=exports\nouveau-dossier.CAR

python car_tool.py generate-from-excel --template "%TEMPLATE%" --excel "%EXCEL%" --output "%OUTPUT%"
if errorlevel 1 (
  echo.
  echo Erreur pendant la generation du CAR.
  pause
  exit /b 1
)

echo.
echo CAR cree : %OUTPUT%
echo Vous pouvez maintenant importer ce fichier dans WinDiagnostics.
pause
