from flask import Flask, render_template, request, jsonify, send_file
from pathlib import Path
import json
import shutil
import subprocess
import sys
import threading
import webbrowser
from datetime import datetime
from windiag_core import build_car_from_template, CAR_FIELD_MAP

# Support PyInstaller
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
    TEMPLATE_FOLDER = Path(sys._MEIPASS) / 'templates'
else:
    BASE_DIR = Path(__file__).parent
    TEMPLATE_FOLDER = BASE_DIR / 'templates'

app = Flask(__name__, template_folder=str(TEMPLATE_FOLDER))
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

BROUILLONS_DIR = BASE_DIR / "brouillons"
EXPORTS_DIR   = BASE_DIR / "exports"
TEMPLATES_DIR = BASE_DIR / "templates"

BROUILLONS_DIR.mkdir(exist_ok=True)
EXPORTS_DIR.mkdir(exist_ok=True)

DIAGNOSTIC_TYPES = {
    "dpe":        {"label": "DPE (Diagnostic Performance Energetique)", "color": "#4CAF50"},
    "termite":    {"label": "Termite",      "color": "#FF9800"},
    "parasite":   {"label": "Parasite",     "color": "#F44336"},
    "amiante":    {"label": "Amiante",      "color": "#2196F3"},
    "plomb":      {"label": "Plomb",        "color": "#9C27B0"},
    "gaz":        {"label": "Gaz",          "color": "#FF6F00"},
    "electricite":{"label": "Electricite",  "color": "#FFC107"},
}

FIELD_DEFINITIONS = [
    ("reference_dossier",  "Reference dossier"),
    ("donneur_ordre",      "Donneur d'ordre"),
    ("ville_dossier",      "Ville du dossier"),
    ("surface",            "Surface"),
    ("date_commande",      "Date de commande"),
    ("date_visite",        "Date de visite"),
    ("date_rapport",       "Date de rapport"),
    ("proprietaire_nom",   "Proprietaire"),
    ("proprietaire_adresse","Adresse proprietaire"),
    ("proprietaire_cp",    "CP proprietaire"),
    ("proprietaire_ville", "Ville proprietaire"),
    ("bien_rue",           "Rue du bien"),
    ("bien_cp",            "CP du bien"),
    ("bien_ville",         "Ville du bien"),
    ("bien_batiment",      "Batiment / etage"),
    ("bien_lot",           "Lot"),
    ("bien_description",   "Description du bien"),
    ("annee_construction", "Annee de construction"),
    ("type_bien",          "Type de bien"),
    ("categorie_bien",     "Categorie"),
    ("titre_mission",      "Titre mission"),
    ("type_mission",       "Code mission"),
    ("date_mission",       "Date mission"),
]


@app.route("/")
def index():
    templates = sorted([f.stem for f in TEMPLATES_DIR.glob("*.CAR")])
    return render_template("index.html", fields=FIELD_DEFINITIONS, templates=templates, diagnostic_types=DIAGNOSTIC_TYPES)


@app.route("/api/brouillons", methods=["GET"])
def list_brouillons():
    brouillons = []
    for path in sorted(BROUILLONS_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        brouillons.append({"nom": path.stem, "date": path.stat().st_mtime,
                           "titre": data.get("titre_mission", "Sans titre"),
                           "type": data.get("diagnostic_type", "?")})
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
    template_nom  = data.get("template")
    diagnostic_type = data.get("diagnostic_type")
    fields_data   = data.get("fields", {})
    nom_sortie    = data.get("nom_sortie", f"dossier-{datetime.now().strftime('%Y%m%d-%H%M%S')}")

    if not template_nom:
        templates = sorted([f.stem for f in TEMPLATES_DIR.glob("*.CAR")])
        if templates:
            template_nom = templates[0]

    if not diagnostic_type:
        return jsonify({"error": "Type de diagnostic requis"}), 400

    template_path = TEMPLATES_DIR / f"{template_nom}.CAR"
    if not template_path.exists():
        return jsonify({"error": f"Template {template_nom} non trouve"}), 404

    filtered_data = {k: v for k, v in fields_data.items() if v and k in CAR_FIELD_MAP}
    output_path   = EXPORTS_DIR / f"{nom_sortie}.CAR"

    try:
        build_car_from_template(template_path, filtered_data, output_path)

        # Si un dossier de destination est spécifié, on y copie le fichier
        save_path = data.get("save_path", "").strip() if data.get("save_path") else ""
        if save_path:
            dest_dir = Path(save_path)
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_file = dest_dir / f"{nom_sortie}.CAR"
            shutil.copy2(output_path, dest_file)
            return jsonify({
                "ok": True,
                "enregistre": True,
                "fichier": f"{nom_sortie}.CAR",
                "chemin": str(dest_file)
            })

        return jsonify({
            "ok": True,
            "enregistre": False,
            "fichier": f"{nom_sortie}.CAR",
            "chemin": str(output_path)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/parcourir-dossier", methods=["GET"])
def parcourir_dossier():
    """Ouvre le sélecteur de dossier Windows et retourne le chemin choisi."""
    try:
        script = (
            "Add-Type -AssemblyName System.Windows.Forms; "
            "Add-Type -AssemblyName System.Drawing; "
            "$owner = New-Object System.Windows.Forms.Form; "
            "$owner.TopMost = $true; "
            "$owner.Opacity = 0; "
            "$owner.ShowInTaskbar = $false; "
            "$owner.Size = New-Object System.Drawing.Size(1,1); "
            "$owner.StartPosition = 'CenterScreen'; "
            "$owner.Show(); [void]$owner.Focus(); "
            "$d = New-Object System.Windows.Forms.OpenFileDialog; "
            "$d.Title = 'Choisir le dossier de sauvegarde'; "
            "$d.InitialDirectory = [Environment]::GetFolderPath('MyDocuments'); "
            "$d.ValidateNames = $false; "
            "$d.CheckFileExists = $false; "
            "$d.CheckPathExists = $true; "
            "$d.FileName = 'Enregistrer ici'; "
            "if ($d.ShowDialog($owner) -eq 'OK') { Write-Output ([System.IO.Path]::GetDirectoryName($d.FileName)) } "
            "$owner.Dispose()"
        )
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            capture_output=True, text=True, timeout=60
        )
        chemin = result.stdout.strip()
        if chemin:
            return jsonify({"chemin": chemin})
        return jsonify({"chemin": None})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/telecharger/<nom>", methods=["GET"])
def telecharger_car(nom):
    path = EXPORTS_DIR / f"{nom}"
    if not path.exists():
        return jsonify({"error": "Fichier non trouve"}), 404
    return send_file(path, as_attachment=True, download_name=nom)


def open_browser():
    import webbrowser
    webbrowser.open("http://127.0.0.1:5000")


if __name__ == "__main__":
    from waitress import serve
    threading.Timer(1.5, open_browser).start()
    print("Serveur démarré sur http://127.0.0.1:5000")
    serve(app, host="127.0.0.1", port=5000)
