from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree
from xml.sax.saxutils import escape

from windiag_core import (
    FIELD_DEFINITIONS,
    build_car_from_template,
    create_blank_car_template,
    extract_car_pieces,
    extract_car_summary,
)
PROMPT_FIELDS = FIELD_DEFINITIONS

NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_PACKAGE_REL = "http://schemas.openxmlformats.org/package/2006/relationships"


def inspect_car(path: Path) -> None:
    print(json.dumps(extract_car_summary(path), ensure_ascii=False, indent=2))


def inspect_car_pieces(path: Path) -> None:
    pieces = extract_car_pieces(path)
    rows = [
        {
            "type": piece.kind,
            "nom": piece.name,
            "surface": piece.surface,
            "exclu": piece.excluded,
            "carrez": piece.carrez,
            "code": piece.code,
        }
        for piece in pieces
    ]
    print(json.dumps(rows, ensure_ascii=False, indent=2))


def generate_car(template: Path, data_path: Path, output: Path) -> None:
    data = json.loads(data_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not all(isinstance(key, str) and isinstance(value, str) for key, value in data.items()):
        raise SystemExit("Le fichier JSON doit contenir un objet simple {champ: valeur}.")

    output.parent.mkdir(parents=True, exist_ok=True)
    build_car_from_template(template, data, output)
    print(output)


def column_name(index: int) -> str:
    name = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        name = chr(65 + remainder) + name
    return name


def xlsx_cell(row_index: int, column_index: int, value: str) -> str:
    ref = f"{column_name(column_index)}{row_index}"
    escaped = escape(value)
    return f'<c r="{ref}" t="inlineStr"><is><t>{escaped}</t></is></c>'


def xlsx_row(row_index: int, values: list[str]) -> str:
    cells = "".join(xlsx_cell(row_index, index, value) for index, value in enumerate(values, start=1))
    return f'<row r="{row_index}">{cells}</row>'


def write_xlsx(path: Path, rows: list[list[str]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet_rows = "".join(xlsx_row(index, row) for index, row in enumerate(rows, start=1))
    sheet_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<worksheet xmlns="{NS_MAIN}" xmlns:r="{NS_REL}">'
        '<cols><col min="1" max="1" width="24" customWidth="1"/>'
        '<col min="2" max="2" width="34" customWidth="1"/>'
        '<col min="3" max="3" width="70" customWidth="1"/></cols>'
        f"<sheetData>{sheet_rows}</sheetData>"
        "</worksheet>"
    )
    workbook_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<workbook xmlns="{NS_MAIN}" xmlns:r="{NS_REL}">'
        '<sheets><sheet name="Saisie CAR" sheetId="1" r:id="rId1"/></sheets>'
        "</workbook>"
    )
    workbook_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<Relationships xmlns="{NS_PACKAGE_REL}">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
        'Target="worksheets/sheet1.xml"/>'
        "</Relationships>"
    )
    root_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<Relationships xmlns="{NS_PACKAGE_REL}">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="xl/workbook.xml"/>'
        "</Relationships>"
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        "</Types>"
    )

    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as xlsx:
        xlsx.writestr("[Content_Types].xml", content_types)
        xlsx.writestr("_rels/.rels", root_rels)
        xlsx.writestr("xl/workbook.xml", workbook_xml)
        xlsx.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        xlsx.writestr("xl/worksheets/sheet1.xml", sheet_xml)
    return path


def cell_text(cell: ElementTree.Element) -> str:
    if cell.attrib.get("t") == "inlineStr":
        return "".join(text.text or "" for text in cell.findall(f".//{{{NS_MAIN}}}t"))
    value = cell.find(f"{{{NS_MAIN}}}v")
    return "" if value is None or value.text is None else value.text


def read_xlsx_rows(path: Path) -> list[list[str]]:
    with zipfile.ZipFile(path) as xlsx:
        sheet_xml = xlsx.read("xl/worksheets/sheet1.xml")

    root = ElementTree.fromstring(sheet_xml)
    rows: list[list[str]] = []
    for row in root.findall(f".//{{{NS_MAIN}}}row"):
        values: dict[int, str] = {}
        for cell in row.findall(f"{{{NS_MAIN}}}c"):
            ref = cell.attrib.get("r", "")
            match = re.match(r"([A-Z]+)", ref)
            if not match:
                continue
            column = 0
            for letter in match.group(1):
                column = column * 26 + ord(letter) - 64
            values[column] = cell_text(cell)
        if values:
            rows.append([values.get(index, "") for index in range(1, max(values) + 1)])
    return rows


def create_excel_template(template: Path, output: Path) -> None:
    defaults = extract_car_summary(template)
    rows = [["Champ", "Libelle", "Valeur"]]
    for key, label in FIELD_DEFINITIONS:
        rows.append([key, label, defaults.get(key, "")])

    write_xlsx(output, rows)
    print(output)


def generate_car_from_excel(template: Path, excel: Path, output: Path) -> None:
    data: dict[str, str] = {}
    for row in read_xlsx_rows(excel)[1:]:
        if len(row) < 3:
            continue
        key, _label, value = row[:3]
        if key:
            data[key] = value

    output.parent.mkdir(parents=True, exist_ok=True)
    build_car_from_template(template, data, output)
    print(output)


def blank_template(source: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    create_blank_car_template(source, output)
    print(output)


def prompt_value(label: str, default: str) -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{label}{suffix}: ").strip()
    return value if value else default


def prompt_car(template: Path, output: Path) -> None:
    defaults = extract_car_summary(template)
    data: dict[str, str] = {}
    print("Saisie du dossier CAR. Appuie sur Entree pour garder la valeur du modele.\n")
    for key, label in PROMPT_FIELDS:
        data[key] = prompt_value(label, defaults.get(key, ""))

    output.parent.mkdir(parents=True, exist_ok=True)
    build_car_from_template(template, data, output)
    print(f"\nFichier CAR cree: {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspecter ou generer des fichiers Wincarez/WinDiagnostics .CAR.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="Afficher les champs principaux d'un .CAR.")
    inspect_parser.add_argument("path", type=Path)

    pieces_parser = subparsers.add_parser("pieces", help="Afficher les pieces/surfaces d'un .CAR enrichi.")
    pieces_parser.add_argument("path", type=Path)

    generate_parser = subparsers.add_parser("generate", help="Generer un .CAR depuis un modele et un JSON.")
    generate_parser.add_argument("--template", type=Path, required=True)
    generate_parser.add_argument("--data", type=Path, required=True)
    generate_parser.add_argument("--output", type=Path, required=True)

    prompt_parser = subparsers.add_parser("prompt", help="Saisir les champs principaux et creer un .CAR.")
    prompt_parser.add_argument("--template", type=Path, required=True)
    prompt_parser.add_argument("--output", type=Path, required=True)

    excel_template_parser = subparsers.add_parser("excel-template", help="Creer un fichier Excel de saisie.")
    excel_template_parser.add_argument("--template", type=Path, required=True)
    excel_template_parser.add_argument("--output", type=Path, required=True)

    excel_generate_parser = subparsers.add_parser("generate-from-excel", help="Creer un .CAR depuis un Excel de saisie.")
    excel_generate_parser.add_argument("--template", type=Path, required=True)
    excel_generate_parser.add_argument("--excel", type=Path, required=True)
    excel_generate_parser.add_argument("--output", type=Path, required=True)

    blank_parser = subparsers.add_parser("blank-template", help="Creer un template CAR vierge depuis un template complet.")
    blank_parser.add_argument("--source", type=Path, required=True)
    blank_parser.add_argument("--output", type=Path, required=True)

    args = parser.parse_args()
    if args.command == "inspect":
        inspect_car(args.path)
    elif args.command == "pieces":
        inspect_car_pieces(args.path)
    elif args.command == "generate":
        generate_car(args.template, args.data, args.output)
    elif args.command == "prompt":
        prompt_car(args.template, args.output)
    elif args.command == "excel-template":
        create_excel_template(args.template, args.output)
    elif args.command == "generate-from-excel":
        generate_car_from_excel(args.template, args.excel, args.output)
    elif args.command == "blank-template":
        blank_template(args.source, args.output)


if __name__ == "__main__":
    main()


def validate_template(path: Path) -> None:
    """Valider qu'un template CAR a tous les champs requis."""
    from windiag_core import CAR_FIELD_MAP, extract_car_summary, read_car_fields
    
    fields = read_car_fields(path)
    summary = extract_car_summary(path)
    
    print(f"\n📊 VALIDATION DU TEMPLATE: {path.name}")
    print("="*60)
    print(f"Nombre de champs: {len(fields)}")
    print(f"Nombre de champs mappés: {len(summary)}\n")
    
    # Vérifier les champs critiques
    critical_fields = [
        "logiciel",
        "donneur_ordre",
        "titre_mission",
        "type_mission",
        "reference_dossier",
        "date_mission",
    ]
    
    print("CHAMPS CRITIQUES:")
    for field in critical_fields:
        value = summary.get(field, "")
        status = "✅" if value and value.strip() else "⚠️"
        print(f"  {status} {field:25} : {value[:40] if value else 'VIDE'}")
    
    # Vérifier la longueur minimale
    min_length = max(CAR_FIELD_MAP.values()) + 1
    print(f"\nLONGUEUR DU FICHIER:")
    print(f"  Minimum requis: {min_length}")
    print(f"  Actuel: {len(fields)}")
    
    if len(fields) < min_length:
        print(f"  ❌ ERREUR: Fichier trop court!")
    else:
        print(f"  ✅ OK")
    
    # Afficher les champs mappés
    print(f"\nCHAMPS DISPONIBLES ({len(summary)}):")
    for i, (key, value) in enumerate(sorted(summary.items()), 1):
        if i > 20:
            print(f"  ... et {len(summary) - 20} autres")
            break
        print(f"  - {key}")


# Ajouter la commande validate
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inspecter ou generer des fichiers Wincarez/WinDiagnostics .CAR.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # ... (autres parsers)
    
    validate_parser = subparsers.add_parser("validate", help="Valider un template CAR.")
    validate_parser.add_argument("path", type=Path)

    args = parser.parse_args()
    
    # ... (autres commandes)
    
    if args.command == "validate":
        validate_template(args.path)
