# 🚀 WinDiag - Générateur CAR

Application web simple pour générer des fichiers `.CAR` Wincarez/WinDiagnostics sans connaissance technique.

## ⚡ Démarrage rapide

### Windows

**Double-cliquer sur :** `windows\run.bat`

C'est tout ! Le navigateur s'ouvre automatiquement.

### Mac / Linux

```bash
./run.sh
```

## 🎯 Utilisation

1. **Sélectionner un template** → Choisir le fichier modèle `.CAR`
2. **Remplir les champs** → Compléter les informations du dossier
3. **Sauvegarder un brouillon** (optionnel) → Pour continuer plus tard
4. **Générer le CAR** → Créer le fichier final
5. **Télécharger** → Le fichier est prêt à utiliser dans WinDiagnostics

## 🖼️ OCR image vers texte

Pour extraire le texte d'une image sur Windows :

```text
windows\OCR-image-vers-texte.bat
```

L'utilisateur double-clique sur ce fichier, glisse/depose l'image dans la fenetre, puis l'outil cree un fichier `.txt`.

Ce module utilise **Tesseract OCR**. S'il n'est pas installe, le lanceur affiche le lien d'installation.

Important : Tesseract fonctionne bien avec du texte imprime ou une photo tres nette. Pour des notes manuscrites de terrain, le resultat peut etre approximatif.

## 💾 Brouillons

Les brouillons sont automatiquement sauvegardés en local sur l'ordinateur :
- **Sauvegarder** : bouton "Sauvegarder" dans la barre latérale
- **Charger** : cliquer sur un brouillon existant
- **Supprimer** : bouton "✕" sur chaque brouillon

Les brouillons ne sont pas supprimés lors de la génération du CAR.

## 📁 Structure

```
├── app.py              ← Application principal
├── run.sh              ← Lancer sur Mac/Linux
├── windows/
│   └── run.bat         ← Lancer sur Windows
├── templates/          ← Fichiers modèles .CAR
│   └── 2025-1285-32.CAR
├── exports/            ← Fichiers .CAR générés
├── brouillons/         ← Brouillons sauvegardés (créé auto)
└── requirements.txt    ← Dépendances Python
```

## ⚙️ Installation (une seule fois)

Si vous double-cliquez sur `run.bat` et ça ne fonctionne pas :

1. **Installer Python**
   - Télécharger depuis https://www.python.org
   - Pendant l'installation, cocher "Add Python to PATH"

2. **Les dépendances s'installent automatiquement** au premier lancement

## 🔧 Développement

```bash
# Installation dépendances
pip install -r requirements.txt

# Lancer l'app
python app.py
```

L'app est accessible à `http://127.0.0.1:5000`

## 📦 Compilation en .EXE (optionnel)

Pour les utilisateurs sans Python :

```bash
pip install pyinstaller
pyinstaller --onefile --icon=icon.ico app.py
```

Le fichier `app.exe` peut être distribué seul.

## 🐛 Dépannage

**"Python n'est pas trouvé"**
→ Installer Python depuis https://www.python.org (cocher "Add to PATH")

**"Erreur: Port 5000 déjà utilisé"**
→ Modifier dans `app.py` ligne 63 : `port=5001` (ou autre)

**"Template non trouvé"**
→ Placer les fichiers `.CAR` dans le dossier `templates/`

## 📝 Format des templates

Les fichiers `.CAR` doivent être dans le dossier `templates/`.

Vous pouvez créer de nouveaux templates avec WinDiagnostics et les ajouter ici.

Un template vierge basé sur la version la plus complète est disponible :

```text
templates/template-vierge-max.CAR
```

Il conserve la structure enrichie du fichier `2026-0218.CAR`, avec les champs dossier principaux vidés et les emplacements `$Pieces` / `$PiecesA` conservés.

### Variante `.CAR` enrichie

Certains fichiers `.CAR`, comme `2026-0218.CAR`, contiennent aussi une liste de pièces à la fin du fichier :

- marqueurs `$Pieces`
- marqueurs `$PiecesA`
- fin de bloc `$Fin`

Pour les analyser en ligne de commande :

```bash
python car_tool.py pieces "C:\chemin\2026-0218.CAR"
```

## 📧 Support

Pour les problèmes, créer une issue sur GitHub.
