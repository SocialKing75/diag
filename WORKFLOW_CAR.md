# Workflow de génération des fichiers CAR

## Structure du projet

```
saisies/
  └── _TEMPLATE.xlsx      ← Fichier modèle (ne pas supprimer)

exports/
  └── [fichiers générés]  ← Les .CAR finaux

templates/
  └── 2025-1285-32.CAR    ← Template de référence
```

## Utilisation

### Pour les utilisateurs (remplissage des données)

1. **Dupliquer le fichier template :**
   - Aller dans le dossier `saisies/`
   - Dupliquer `_TEMPLATE.xlsx`
   - Renommer : `affaire_001.xlsx`, `affaire_002.xlsx`, etc.

2. **Remplir les données :**
   - Ouvrir le fichier Excel
   - Remplir la colonne "Valeur" pour chaque champ
   - Sauvegarder et fermer

### Pour la génération des CAR

**Une fois tous les fichiers Excel remplis, lancer :**

```bash
./generate_all.sh
```

Cela va :
- Lire tous les Excel dans `saisies/` (sauf le template)
- Générer les fichiers `.CAR` correspondants dans `exports/`
- Afficher un résumé

## Exemple

```
saisies/
  ├── _TEMPLATE.xlsx
  ├── affaire_001.xlsx      ← Affaire Paris
  ├── affaire_002.xlsx      ← Affaire Lyon
  └── affaire_003.xlsx      ← Affaire Marseille
```

Après `./generate_all.sh` :

```
exports/
  ├── affaire_001.CAR
  ├── affaire_002.CAR
  └── affaire_003.CAR
```

## Points importants

- Ne pas modifier le fichier `_TEMPLATE.xlsx` (ou l'overwrite se fera)
- Les noms des fichiers Excel deviennent les noms des CAR (ex: `test.xlsx` → `test.CAR`)
- Le script ignore automatiquement les fichiers contenant "_TEMPLATE" dans le nom
