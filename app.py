from flask import Flask, render_template, request, jsonify, send_file
from pathlib import Path
import json
from datetime import datetime
from windiag_core import build_car_from_template, extract_car_summary, CAR_FIELD_MAP

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max

BROUILLONS_DIR = Path("brouillons")
EXPORTS_DIR = Path("exports")
TEMPLATES_DIR = Path("templates")

BROUILLONS_DIR.mkdir(exist_ok=True)
EXPORTS_DIR.mkdir(exist_ok=True)

DIAGNOSTIC_TYPES = {
    "dpe": {"label": "DPE (Diagnostic Performance Energetique)", "color": "#4CAF50"},
    "termite": {"label": "Termite", "color": "#FF9800"},
    "parasite": {"label": "Parasite", "color": "#F44336"},
    "amiante": {"label": "Amiante", "color": "#2196F3"},
    "plomb": {"label": "Plomb", "color": "#9C27B0"},
    "gaz": {"label": "Gaz", "color": "#FF6F00"},
    "electricite": {"label": "Electricite", "color": "#FFC107"},
}

FIELD_DEFINITIONS = [
    ("reference_dossier", "Reference dossier"),
    ("donneur_ordre", "Donneur d'ordre"),
    ("ville_dossier", "Ville du dossier"),
    ("surface", "Surface"),
    ("date_commande", "Date de commande"),
    ("date_visite", "Date de visite"),
    ("date_rapport", "Date de rapport"),
    ("proprietaire_nom", "Proprietaire"),
    ("proprietaire_adresse", "Adresse proprietaire"),
    ("proprietaire_cp", "CP proprietaire"),
    ("proprietaire_ville", "Ville proprietaire"),
    ("bien_rue", "Rue du bien"),
    ("bien_cp", "CP du bien"),
    ("bien_ville", "Ville du bien"),
    ("bien_batiment", "Batiment / etage"),
    ("bien_lot", "Lot"),
    ("bien_description", "Description du bien"),
    ("annee_construction", "Annee de construction"),
    ("type_bien", "Type de bien"),
    ("categorie_bien", "Categorie"),
    ("titre_mission", "Titre mission"),
    ("type_mission", "Code mission"),
    ("date_mission", "Date mission"),
]


@app.route("/")
def index():
    brouillons = sorted([f.stem for f in BROUILLONS_DIR.glob("*.json")])
    templates = sorted([f.stem for f in TEMPLATES_DIR.glob("*.CAR")])
    return render_template("index.html", fields=FIELD_DEFINITIONS, brouillons=brouillons, templates=templates, diagnostic_types=DIAGNOSTIC_TYPES)


@app.route("/api/brouillons", methods=["GET"])
def list_brouillons():
    brouillons = []
    for path in sorted(BROUILLONS_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        brouillons.append({
            "nom": path.stem,
            "date": path.stat().st_mtime,
            "titre": data.get("titre_mission", "Sans titre"),
            "type": data.get("diagnostic_type", "?")
        })
    return jsonify(sorted(brouillons, key=lambda x: x["date"], reverse=True))


@app.route("/api/brouillons/<nom>", methods=["GET"])
def load_brouillon(nom):
    path = BROUILLONS_DIR / f"{nom}.json"
    if not path.exists():
        return jsonify({"error": "Brouillon non trouve"}), 404
    return jsonify(json.loads(path.read_text(encoding="utf-8")))


@app.route("/api/brouillons", methods=["POST"])
def save_brouillon():
    data = request.json
    nom = data.get("nom", f"brouillon-{datetime.now().strftime('%Y%m%d-%H%M%S')}")

    path = BROUILLONS_DIR / f"{nom}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    return jsonify({"ok": True, "nom": nom})


@app.route("/api/brouillons/<nom>", methods=["DELETE"])
def delete_brouillon(nom):
    path = BROUILLONS_DIR / f"{nom}.json"
    if path.exists():
        path.unlink()
    return jsonify({"ok": True})


@app.route("/api/generer", methods=["POST"])
def generer_car():
    data = request.json
    template_nom = data.get("template")
    diagnostic_type = data.get("diagnostic_type")
    fields_data = data.get("fields", {})
    nom_sortie = data.get("nom_sortie", f"dossier-{datetime.now().strftime('%Y%m%d-%H%M%S')}")

    if not template_nom:
        return jsonify({"error": "Pas de template selectionne"}), 400
    
    if not diagnostic_type:
        return jsonify({"error": "Type de diagnostic requis"}), 400

    template_path = TEMPLATES_DIR / f"{template_nom}.CAR"
    if not template_path.exists():
        return jsonify({"error": f"Template {template_nom} non trouve"}), 404

    # Filtrer les champs vides et les champs inconnus
    filtered_data = {k: v for k, v in fields_data.items() if v and k in CAR_FIELD_MAP}
    # Diagnostic type est juste pour la saisie, pas pour le CAR

    output_path = EXPORTS_DIR / f"{nom_sortie}.CAR"

    try:
        build_car_from_template(template_path, filtered_data, output_path)
        return jsonify({
            "ok": True,
            "fichier": f"{nom_sortie}.CAR",
            "chemin": str(output_path)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/telecharger/<nom>", methods=["GET"])
def telecharger_car(nom):
    path = EXPORTS_DIR / f"{nom}"
    if not path.exists():
        return jsonify({"error": "Fichier non trouve"}), 404
    return send_file(path, as_attachment=True, download_name=nom)


if __name__ == "__main__":
    app.run(debug=False, host="127.0.0.1", port=5000)
