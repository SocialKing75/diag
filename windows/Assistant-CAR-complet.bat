@echo off
setlocal
cd /d "%~dp0\.."

echo.
echo ==================================
echo  Assistant CAR complet
echo ==================================
echo.
echo Ce workflow fait tout en une seule fois :
echo 1. Creation de l'Excel
echo 2. Ouverture de l'Excel
echo 3. Generation du CAR apres saisie
echo.

set /p TEMPLATE=Glisser/deposer le modele .CAR ici puis Entrer : 
if "%TEMPLATE%"=="" (
  echo Aucun modele indique.
  pause
  exit /b 1
)

set TEMPLATE=%TEMPLATE:"=%

set /p EXCEL=Fichier Excel de saisie [exports\saisie-car.xlsx] : 
if "%EXCEL%"=="" set EXCEL=exports\saisie-car.xlsx

set /p OUTPUT=Fichier CAR final [exports\nouveau-dossier.CAR] : 
if "%OUTPUT%"=="" set OUTPUT=exports\nouveau-dossier.CAR

echo.
echo Creation de l'Excel...
python car_tool.py excel-template --template "%TEMPLATE%" --output "%EXCEL%"
if errorlevel 1 (
  echo.
  echo Erreur pendant la creation de l'Excel.
  pause
  exit /b 1
)

echo.
echo L'Excel va s'ouvrir.
echo Remplir la colonne Valeur, enregistrer, fermer Excel, puis revenir ici.
start "" "%EXCEL%"
pause

echo.
echo Generation du CAR...
python car_tool.py generate-from-excel --template "%TEMPLATE%" --excel "%EXCEL%" --output "%OUTPUT%"
if errorlevel 1 (
  echo.
  echo Erreur pendant la generation du CAR.
  pause
  exit /b 1
)

echo.
echo Terminé.
echo Fichier CAR cree : %OUTPUT%
echo Vous pouvez maintenant l'importer dans WinDiagnostics.
pause
