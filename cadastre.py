"""Récupération automatique de la référence cadastrale (section + parcelle)
à partir d'une adresse, via deux API publiques gratuites (aucune clé requise) :

  1. BAN  (api-adresse.data.gouv.fr) : adresse -> coordonnées (lon, lat)
  2. IGN Carto Cadastre (apicarto.ign.fr) : point -> parcelle(s) {section, numéro}
"""

import json

import requests

BAN_URL = "https://api-adresse.data.gouv.fr/search/"
IGN_URL = "https://apicarto.ign.fr/api/cadastre/parcelle"
TIMEOUT = 20


def geocoder_adresse(adresse: str, code_postal: str = "", ville: str = ""):
    """Adresse texte -> (lon, lat, label). Renvoie None si rien trouvé."""
    q = " ".join(p for p in (adresse, code_postal, ville) if p).strip()
    if not q:
        return None
    params = {"q": q, "limit": 1}
    # Si on a un code postal, on restreint au bon code INSEE/CP pour fiabiliser
    if code_postal:
        params["postcode"] = code_postal
    r = requests.get(BAN_URL, params=params, timeout=TIMEOUT)
    r.raise_for_status()
    feats = r.json().get("features", [])
    if not feats:
        return None
    f = feats[0]
    lon, lat = f["geometry"]["coordinates"]
    return lon, lat, f["properties"].get("label", q)


def _carre_autour(lon: float, lat: float, rayon_m: float) -> str:
    """Construit un petit polygone carré (GeoJSON) centré sur le point.
    Sert de zone de recherche quand le point tombe sur la voirie."""
    import math
    dlat = rayon_m / 111_320.0
    dlon = rayon_m / (111_320.0 * math.cos(math.radians(lat)) or 1e-9)
    coords = [
        [lon - dlon, lat - dlat],
        [lon + dlon, lat - dlat],
        [lon + dlon, lat + dlat],
        [lon - dlon, lat + dlat],
        [lon - dlon, lat - dlat],
    ]
    return json.dumps({"type": "Polygon", "coordinates": [coords]})


def _interroger_ign(geom: str):
    r = requests.get(IGN_URL, params={"geom": geom}, timeout=TIMEOUT)
    r.raise_for_status()
    parcelles = []
    for f in r.json().get("features", []):
        p = f.get("properties", {})
        section = p.get("section", "")
        numero = p.get("numero", "")
        parcelles.append({
            "commune": p.get("nom_com") or p.get("code_insee") or "",
            "code_insee": p.get("code_insee", ""),
            "section": section,
            "numero": numero,
            "contenance": p.get("contenance"),  # surface parcelle en m²
            "reference": f"{section} {numero}".strip(),
            "idu": p.get("idu", ""),            # identifiant cadastral complet
            "geometry": f.get("geometry"),      # polygone GeoJSON pour la carte
        })
    return parcelles


def reference_cadastrale(adresse: str, code_postal: str = "", ville: str = ""):
    """Renvoie un dict :
        {
          "ok": True,
          "adresse_trouvee": "...",
          "approx": False,            # True si trouvé via élargissement de zone
          "parcelles": [ {commune, section, numero, contenance, reference, idu}, ... ]
        }
    ou {"ok": False, "error": "..."}.
    """
    try:
        coords = geocoder_adresse(adresse, code_postal, ville)
    except requests.RequestException as e:
        return {"ok": False, "error": f"Géocodage indisponible ({e})"}

    if not coords:
        return {"ok": False, "error": "Adresse introuvable (BAN)"}

    lon, lat, label = coords

    try:
        # 1. Essai précis : le point doit tomber dans une parcelle
        parcelles = _interroger_ign(
            json.dumps({"type": "Point", "coordinates": [lon, lat]}))
        approx = False
        # 2. Sinon, on élargit progressivement (point souvent posé sur la voirie)
        for rayon in (12, 25, 50):
            if parcelles:
                break
            parcelles = _interroger_ign(_carre_autour(lon, lat, rayon))
            approx = bool(parcelles)
    except requests.RequestException as e:
        return {"ok": False, "error": f"API cadastre indisponible ({e})"}

    if not parcelles:
        return {"ok": False, "error": "Aucune parcelle à proximité",
                "adresse_trouvee": label}

    # Dédoublonnage (l'élargissement peut renvoyer des doublons)
    vus, uniques = set(), []
    for p in parcelles:
        if p["idu"] and p["idu"] in vus:
            continue
        vus.add(p["idu"])
        uniques.append(p)

    return {"ok": True, "adresse_trouvee": label, "approx": approx,
            "point": [lon, lat],   # point géocodé (pour centrer la carte)
            "parcelles": uniques}


if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    res = reference_cadastrale(*args) if args else reference_cadastrale(
        "6 Parvis Notre-Dame", "75004", "Paris")
    print(json.dumps(res, ensure_ascii=False, indent=2))
