@echo off
chcp 65001 >nul
set "PYTHONUTF8=1"
cd /d "%~dp0.."

echo.
echo ====================================
echo   Bot Telegram - Classement photos
echo ====================================
echo.
echo Dossier projet : %CD%
echo.

if not exist ".env" (
    echo ERREUR: fichier .env manquant dans ce dossier.
    echo.
    echo Copier .env.example en .env et remplir:
    echo   - TELEGRAM_BOT_TOKEN  ^(via @BotFather sur Telegram^)
    echo   - OPEN_IA             ^(cle OpenAI, https://platform.openai.com^)
    echo.
    pause
    exit /b 1
)

set "VP=venv\Scripts\python.exe"
if not exist "%VP%" (
    echo ERREUR: environnement Python non trouve ^(venv^).
    echo Lance d'abord windows\run.bat pour l'installer.
    pause
    exit /b 1
)

echo Arret des eventuelles instances du bot deja en cours...
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -match 'bot_telegram' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }" >nul 2>&1

echo Verification des dependances...
"%VP%" -m pip install --quiet --disable-pip-version-check python-dotenv openai requests

echo.
echo Bot demarre. Laisse cette fenetre ouverte.
echo Ctrl+C pour arreter.
echo.

"%VP%" bot_telegram.py

echo.
echo === Le bot s'est arrete (erreur ci-dessus ou Ctrl+C). ===
pause
