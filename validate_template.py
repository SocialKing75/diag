#!/usr/bin/env python3
"""Valider qu'un template CAR a tous les champs requis."""

import sys
from pathlib import Path
from windiag_core import CAR_FIELD_MAP, extract_car_summary, read_car_fields


def validate(template_path: Path) -> bool:
    """Valider un template CAR."""
    if not template_path.exists():
        print(f"❌ Fichier non trouvé: {template_path}")
        return False
    
    try:
        fields = read_car_fields(template_path)
        summary = extract_car_summary(template_path)
    except Exception as e:
        print(f"❌ Erreur de lecture: {e}")
        return False
    
    print(f"\n{'='*60}")
    print(f"VALIDATION: {template_path.name}")
    print(f"{'='*60}\n")
    
    # Statistiques
    print(f"📊 Statistiques:")
    print(f"   Total champs: {len(fields)}")
    print(f"   Mappés: {len(summary)}")
    print()
    
    # Vérifier les champs critiques
    critical_fields = [
        ("logiciel", "Logiciel (Wincarez 8.0)"),
        ("donneur_ordre", "Donneur d'ordre"),
        ("titre_mission", "Titre de la mission"),
        ("type_mission", "Code de mission (DPE, DX, etc)"),
        ("reference_dossier", "Référence du dossier"),
        ("date_mission", "Date de mission"),
        ("categorie_bien", "Catégorie du bien"),
        ("type_bien", "Type de bien"),
    ]
    
    print("🔍 Champs critiques:")
    all_ok = True
    for field, label in critical_fields:
        value = summary.get(field, "")
        if value and value.strip():
            print(f"   ✅ {field:20} - {label}")
        else:
            print(f"   ⚠️  {field:20} - {label} (VIDE)")
            all_ok = False
    
    # Vérifier la longueur minimale
    print()
    min_length = max(CAR_FIELD_MAP.values()) + 1
    print(f"📏 Longueur du fichier:")
    print(f"   Minimum: {min_length}")
    print(f"   Actuel: {len(fields)}")
    
    if len(fields) < min_length:
        print(f"   ❌ ERREUR: Trop court de {min_length - len(fields)} champs")
        all_ok = False
    else:
        print(f"   ✅ OK")
    
    # Résumé
    print()
    if all_ok:
        print("✅ Template valide!")
        return True
    else:
        print("⚠️  Template incomplet. À vérifier dans WinDiagnostics.")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validate_template.py <fichier.CAR>")
        sys.exit(1)
    
    path = Path(sys.argv[1])
    success = validate(path)
    sys.exit(0 if success else 1)
