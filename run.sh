#!/bin/bash

echo ""
echo "===================================="
echo "  Generateur CAR - WinDiag"
echo "===================================="
echo ""

# Vérifier Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 n'est pas installé."
    exit 1
fi

# Installer dépendances si nécessaire
python3 -c "import flask" 2>/dev/null || {
    echo "Installation des dépendances..."
    pip install -r requirements.txt
}

echo ""
echo "Démarrage de l'application..."
echo "Le navigateur va s'ouvrir automatiquement."
echo ""
echo "Appuyer sur Ctrl+C pour arrêter."
echo ""

# Ouvrir le navigateur
if command -v xdg-open &> /dev/null; then
    xdg-open "http://127.0.0.1:5000" &
elif command -v open &> /dev/null; then
    open "http://127.0.0.1:5000" &
fi

# Lancer Flask
python3 app.py
