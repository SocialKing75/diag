from __future__ import annotations

import json
import os
import re
import csv
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path


SKIP_WORDS = {"non", "n", "aucun", "aucune", "-", "skip", "passer"}
CAR_ENCODING = "cp1252"

CAR_FIELD_MAP = {
    "logiciel": 0,
    "donneur_ordre": 1,
    "ville_dossier": 2,
    "surface": 3,
    "reference_commande": 4,
    "date_commande": 5,
    "date_visite": 6,
    "date_rapport": 7,
    "observation_dossier": 8,
    "proprietaire_nom": 9,
    "proprietaire_adresse": 10,
    "proprietaire_cp": 11,
    "proprietaire_ville": 12,
    "proprietaire_tel": 13,
    "proprietaire_email": 15,
    "facturation_adresse": 18,
    "facturation_cp": 19,
    "facturation_ville": 20,
    "facturation_tel": 21,
    "facturation_mobile": 22,
    "facturation_email": 23,
    "bien_rue": 25,
    "bien_cp": 26,
    "bien_ville": 27,
    "bien_batiment": 29,
    "bien_lot": 30,
    "bien_tel": 31,
    "bien_description": 32,
    "honoraires_ttc": 34,
    "honoraires_tva": 35,
    "honoraires_ht": 36,
    "reference_dossier": 41,
    "date_dossier": 42,
    "usage_bien": 46,
    "contact_telephone": 55,
    "annee_construction": 56,
    "type_bien": 57,
    "etage": 58,
    "sous_sol": 59,
    "type_mission": 60,
    "type_mission_secondaire": 61,
    "champ_64": 63,
    "champ_65": 64,
    "contact_nom": 65,
    "contact_acces": 66,
    "etat_bien": 74,
    "categorie_bien": 75,
    "titre_mission": 85,
    "date_mission": 86,
}

BLANK_TEMPLATE_KEEP_FIELDS = {"logiciel"}

FIELD_DEFINITIONS = [
    ("reference_dossier", "Référence dossier"),
    ("date_dossier", "Date dossier"),
    ("donneur_ordre", "Donneur d'ordre"),
    ("ville_dossier", "Ville du dossier"),
    ("surface", "Surface"),
    ("reference_commande", "Référence commande"),
    ("date_commande", "Date de commande"),
    ("date_visite", "Date de visite"),
    ("date_rapport", "Date de rapport"),
    ("observation_dossier", "Observation dossier"),
    ("usage_bien", "Usage du bien"),
    ("proprietaire_nom", "Propriétaire"),
    ("proprietaire_adresse", "Adresse propriétaire"),
    ("proprietaire_cp", "CP propriétaire"),
    ("proprietaire_ville", "Ville propriétaire"),
    ("proprietaire_tel", "Téléphone propriétaire"),
    ("proprietaire_email", "Email propriétaire"),
    ("facturation_adresse", "Adresse facturation"),
    ("facturation_cp", "CP facturation"),
    ("facturation_ville", "Ville facturation"),
    ("facturation_tel", "Téléphone facturation"),
    ("facturation_mobile", "Mobile facturation"),
    ("facturation_email", "Email facturation"),
    ("bien_rue", "Rue du bien"),
    ("bien_cp", "CP du bien"),
    ("bien_ville", "Ville du bien"),
    ("bien_batiment", "Bâtiment / étage"),
    ("bien_lot", "Lot"),
    ("bien_tel", "Téléphone du bien"),
    ("bien_description", "Description du bien"),
    ("annee_construction", "Année de construction"),
    ("type_bien", "Type de bien"),
    ("categorie_bien", "Catégorie"),
    ("etat_bien", "État du bien"),
    ("etage", "Étage"),
    ("sous_sol", "Sous-sol"),
    ("titre_mission", "Titre mission"),
    ("type_mission", "Code mission"),
    ("type_mission_secondaire", "Code mission secondaire"),
    ("date_mission", "Date mission"),
    ("contact_nom", "Contact / accès"),
    ("contact_acces", "Détail accès"),
    ("contact_telephone", "Téléphone contact"),
    ("honoraires_ttc", "Honoraires TTC"),
    ("honoraires_tva", "Honoraires TVA"),
    ("honoraires_ht", "Honoraires HT"),
    ("champ_64", "Champ 64"),
    ("champ_65", "Champ 65"),
]


@dataclass
class Surface:
    area_m2: float
    material: str | None = None


@dataclass
class Room:
    name: str
    floor: Surface
    walls: Surface
    ceiling: Surface
    height_m: float | None = None
    orientation: str | None = None
    joinery: str | None = None


@dataclass
class Dossier:
    name: str
    created_at: str
    rooms: list[Room] = field(default_factory=list)


@dataclass
class CarPiece:
    kind: str
    name: str
    surface: str
    excluded: str
    carrez: str
    code: str


def normalize_optional(text: str) -> str | None:
    value = text.strip()
    if not value or value.lower() in SKIP_WORDS:
        return None
    return value


def parse_number(text: str) -> float | None:
    match = re.search(r"\d+(?:[,.]\d+)?", text)
    if not match:
        return None
    return float(match.group(0).replace(",", "."))


def parse_surface(text: str) -> Surface | None:
    area = parse_number(text)
    if area is None:
        return None

    material = text
    material = re.sub(r"\d+(?:[,.]\d+)?", "", material, count=1)
    material = re.sub(r"\bm2\b|\bm²\b|\bm\b|:", "", material, flags=re.IGNORECASE)
    material = normalize_optional(material)
    return Surface(area_m2=area, material=material)


def read_car_fields(path: str | Path) -> list[str]:
    with Path(path).open("r", encoding=CAR_ENCODING, newline="") as file:
        rows = list(csv.reader(file))

    fields: list[str] = []
    for index, row in enumerate(rows, start=1):
        if len(row) != 1:
            raise ValueError(f"CAR invalide ligne/champ {index}: {len(row)} colonnes")
        fields.append(row[0])
    return fields


def write_car_fields(path: str | Path, fields: list[str]) -> Path:
    output_path = Path(path)
    with output_path.open("w", encoding=CAR_ENCODING, newline="") as file:
        writer = csv.writer(file, lineterminator="\r\n", quoting=csv.QUOTE_ALL)
        for field_value in fields:
            writer.writerow([field_value])
    return output_path


def extract_car_summary(path: str | Path) -> dict[str, str]:
    fields = read_car_fields(path)
    summary: dict[str, str] = {}
    for key, index in CAR_FIELD_MAP.items():
        if index < len(fields):
            summary[key] = fields[index]
    return summary


def extract_car_pieces(path: str | Path) -> list[CarPiece]:
    fields = read_car_fields(path)
    pieces: list[CarPiece] = []
    index = 0
    while index < len(fields):
        marker = fields[index]
        if marker not in {"$Pieces", "$PiecesA"}:
            index += 1
            continue

        block = fields[index + 1 : index + 14]
        pieces.append(
            CarPiece(
                kind=marker.removeprefix("$"),
                name=block[0] if len(block) > 0 else "",
                surface=block[1] if len(block) > 1 else "",
                excluded=block[2] if len(block) > 2 else "",
                carrez=block[3] if len(block) > 3 else "",
                code=block[8] if len(block) > 8 else "",
            )
        )
        index += 14
    return pieces


def build_car_from_template(template_path: str | Path, data: dict[str, str], output_path: str | Path) -> Path:
    fields = read_car_fields(template_path)
    unknown = sorted(set(data) - set(CAR_FIELD_MAP))
    if unknown:
        raise ValueError(f"Champs CAR inconnus: {', '.join(unknown)}")

    for key, value in data.items():
        index = CAR_FIELD_MAP[key]
        if index >= len(fields):
            raise ValueError(f"Le modele CAR est trop court pour le champ {key}")
        fields[index] = value

    return write_car_fields(output_path, fields)


def create_blank_car_template(source_path: str | Path, output_path: str | Path, clear_pieces: bool = True) -> Path:
    fields = read_car_fields(source_path)

    for key, index in CAR_FIELD_MAP.items():
        if key in BLANK_TEMPLATE_KEEP_FIELDS:
            continue
        if index < len(fields):
            fields[index] = ""

    if clear_pieces:
        index = 0
        while index < len(fields):
            if fields[index] not in {"$Pieces", "$PiecesA"}:
                index += 1
                continue

            block_start = index + 1
            for offset in (0, 1, 2, 3):
                if block_start + offset < len(fields):
                    fields[block_start + offset] = ""
            index += 14

    return write_car_fields(output_path, fields)


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip()).strip("-")
    return slug.lower() or "dossier"


def format_surface(surface: Surface) -> str:
    material = f" ({surface.material})" if surface.material else ""
    return f"{surface.area_m2:g} m²{material}"


def format_recap(dossier: Dossier) -> str:
    total_floor = sum(room.floor.area_m2 for room in dossier.rooms)
    total_walls = sum(room.walls.area_m2 for room in dossier.rooms)
    total_ceiling = sum(room.ceiling.area_m2 for room in dossier.rooms)

    lines = [
        f"Dossier : {dossier.name}",
        f"Pièces : {len(dossier.rooms)}",
        "",
        "Récapitulatif pièces",
    ]

    for index, room in enumerate(dossier.rooms, start=1):
        lines.extend(
            [
                "",
                f"{index}. {room.name}",
                f"Sol : {format_surface(room.floor)}",
                f"Murs : {format_surface(room.walls)}",
                f"Plafond : {format_surface(room.ceiling)}",
            ]
        )
        if room.height_m is not None:
            lines.append(f"Hauteur sous plafond : {room.height_m:g} m")
        if room.orientation:
            lines.append(f"Orientation : {room.orientation}")
        if room.joinery:
            lines.append(f"Menuiseries : {room.joinery}")

    lines.extend(
        [
            "",
            "Totaux",
            f"Sol : {total_floor:g} m²",
            f"Murs : {total_walls:g} m²",
            f"Plafonds : {total_ceiling:g} m²",
        ]
    )
    return "\n".join(lines)


def save_json(dossier: Dossier) -> Path:
    output_dir = Path(os.getenv("OUTPUT_DIR", "exports"))
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{slugify(dossier.name)}.json"
    path = output_dir / filename
    path.write_text(
        json.dumps(asdict(dossier), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path
