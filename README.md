# WinDiag Telegram Bot

Bot Telegram pour saisir les pieces sur le terrain et generer un recap pret a coller dans WinDiag, avec un fichier JSON archive par dossier.

## Installation

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Dans `.env`, renseigner :

- `TELEGRAM_BOT_TOKEN` : token donne par BotFather.
- `TELEGRAM_ALLOWED_CHAT_IDS` : optionnel, liste d'IDs Telegram separes par des virgules.
- `OUTPUT_DIR` : optionnel, dossier de sortie des JSON.

## Lancement

```bash
. .venv/bin/activate
python bot.py
```

## Flux inspecteur

1. `/start`
2. Saisie du nom de dossier/logement.
3. Pour chaque piece :
   - nom de piece
   - sol : surface + materiau optionnel
   - murs : surface + materiau optionnel
   - plafond : surface + materiau optionnel
   - hauteur sous plafond optionnelle
   - orientation optionnelle
   - menuiseries optionnelles
4. Boutons `Ajouter une piece`, `Terminer`, `Annuler`.

Le bot envoie :

- un recap texte lisible et pret a coller ;
- un fichier `.json` exploitable par une future auto-saisie Windows.

## Workflow `.CAR`

Les fichiers `.CAR` Wincarez/WinDiagnostics sont des fichiers texte encodes en Windows-1252 avec retours ligne Windows.
Le projet sait maintenant lire les champs principaux, puis generer un nouveau `.CAR` depuis un modele existant.

### Utilisation simple sur Windows

Pour un utilisateur qui ne connait pas Python, utiliser les fichiers dans le dossier `windows` :

- `windows\Assistant-CAR-complet.bat` : workflow complet en une seule fois
- `windows\WinDiag-CAR-menu.bat` : menu principal
- `windows\01-creer-excel-saisie.bat` : creer l'Excel de saisie
- `windows\02-generer-car-depuis-excel.bat` : creer le `.CAR` depuis l'Excel rempli

Le plus simple est de double-cliquer sur `Assistant-CAR-complet.bat`.

Workflow utilisateur :

1. Double-cliquer sur `windows\Assistant-CAR-complet.bat`.
2. Glisser/deposer le fichier modele `.CAR` dans la fenetre.
3. L'Excel s'ouvre automatiquement.
4. Modifier uniquement la colonne `Valeur`.
5. Enregistrer et fermer Excel.
6. Revenir dans la fenetre et appuyer sur une touche.
7. Le `.CAR` final est genere.
8. Importer le `.CAR` dans WinDiagnostics.

Pour une version encore plus simple, on pourra ensuite compiler l'outil en `.exe` Windows avec PyInstaller afin que Python n'ait pas besoin d'etre installe sur les postes utilisateurs.

Inspecter un fichier :

```bash
python3 car_tool.py inspect /home/name/Téléchargements/2025-1285-32.CAR
```

Generer un nouveau fichier depuis un modele :

```bash
python3 car_tool.py generate \
  --template /home/name/Téléchargements/2025-1285-32.CAR \
  --data dossier-car.json \
  --output exports/nouveau-dossier.CAR
```

Saisir les informations au clavier et creer directement le `.CAR` :

```bash
python3 car_tool.py prompt \
  --template /home/name/Téléchargements/2025-1285-32.CAR \
  --output exports/test-saisie.CAR
```

Creer un Excel de saisie :

```bash
python3 car_tool.py excel-template \
  --template /home/name/Téléchargements/2025-1285-32.CAR \
  --output exports/saisie-car.xlsx
```

Dans Excel ou LibreOffice, modifier uniquement la colonne `Valeur`, puis generer le `.CAR` :

```bash
python3 car_tool.py generate-from-excel \
  --template /home/name/Téléchargements/2025-1285-32.CAR \
  --excel exports/saisie-car.xlsx \
  --output exports/depuis-excel.CAR
```

Exemple de `dossier-car.json` :

```json
{
  "donneur_ordre": "GENERALI VIE C/o Generali Real Estate",
  "ville_dossier": "PARIS",
  "surface": "126.60",
  "reference_commande": "",
  "date_commande": "30/01/2026",
  "date_visite": "30/01/2026",
  "date_rapport": "30/01/2026",
  "proprietaire_nom": "GENERALI REAL ESTATE",
  "proprietaire_adresse": "PILLET-WILL",
  "proprietaire_cp": "75009",
  "proprietaire_ville": "PARIS 9",
  "bien_rue": "INGRES",
  "bien_cp": "75016",
  "bien_ville": "PARIS",
  "bien_batiment": "1er Etage",
  "bien_lot": "32 + CAVE LOT N° 6",
  "bien_description": "4 Pièces",
  "annee_construction": "Avant 1948",
  "type_bien": "Habitation (parties privatives d'immeuble collectif d'habitation)",
  "type_mission": "CP",
  "champ_64": "4",
  "categorie_bien": "Appartement",
  "titre_mission": "DDT VENTE SANS CARREZ / LOT N°32",
  "date_mission": "30/01/2026"
}
```

## Commandes

- `/start` : nouveau dossier
- `/cancel` : annuler la saisie en cours
- `/help` : aide rapide
