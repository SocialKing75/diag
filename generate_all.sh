#!/bin/bash

# Générer tous les .CAR depuis les fichiers Excel dans saisies/

TEMPLATE="templates/2025-1285-32.CAR"
SAISIES_DIR="saisies"
EXPORTS_DIR="exports"

if [ ! -f "$TEMPLATE" ]; then
  echo "❌ Template CAR non trouvé: $TEMPLATE"
  exit 1
fi

count=0
for xlsx_file in "$SAISIES_DIR"/*.xlsx; do
  # Ignorer le fichier template
  if [[ "$xlsx_file" == *"_TEMPLATE"* ]]; then
    continue
  fi

  basename=$(basename "$xlsx_file" .xlsx)
  echo "⏳ Génération de $basename..."

  python3 car_tool.py generate-from-excel \
    --template "$TEMPLATE" \
    --excel "$xlsx_file" \
    --output "$EXPORTS_DIR/${basename}.CAR"

  if [ $? -eq 0 ]; then
    echo "✓ $basename"
    ((count++))
  else
    echo "❌ Erreur sur $basename"
  fi
done

echo ""
echo "✓ $count fichier(s) CAR généré(s) dans $EXPORTS_DIR/"
