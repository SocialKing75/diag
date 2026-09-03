"""
Bot Telegram - Classement automatique des photos terrain
- ReÃ§oit photos + "NOM CLIENT ANNEE-REF" via Telegram
- Sauvegarde dans Dropbox\\RAPPORTS 2010\\{CLIENT}\\{REF} PHOTOS\\
- Photo captionnÃ©e "notes" -> extraction Claude Vision -> JSON
"""

import json
import os
import re
import time
import requests
from os import walk
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

import vision

# â”€â”€ Config â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
OPENAI_KEY  = os.getenv("OPEN_IA", "")
BASE_DIR      = Path(os.getenv("RAPPORTS_DIR",
    r"C:\Users\Assistante\Dropbox\Parasitis\RAPPORTS 2010"))
FUZZY_THRESH  = 0.55
CONTEXT_TTL = 300


class Bot:
    """Un bot Telegram = un token + ses URLs + ses contextes utilisateur."""

    def __init__(self, name: str, token: str):
        self.name = name
        self.token = token
        self.tg_url = f"https://api.telegram.org/bot{token}"
        self.tg_file_url = f"https://api.telegram.org/file/bot{token}"
        self.offset = 0
        # Contextes par utilisateur, propres Ã  ce bot
        self.pending: dict[int, dict] = {}
        self.confirming: dict[int, dict] = {}
        self.selecting: dict[int, dict] = {}


def load_bots() -> list["Bot"]:
    """Construit l'unique bot autorise a partir de TELEGRAM_BOT_TOKEN."""
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    return [Bot("Veilleregle_bot", token)] if token else []


# â”€â”€ Recherche dossier client â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def find_client_folder(name: str) -> Path | None:
    name_up = name.upper().strip()
    best: tuple[float, Path | None] = (0.0, None)

    for folder in BASE_DIR.iterdir():
        if not folder.is_dir():
            continue
        folder_up = folder.name.upper()
        if name_up in folder_up or folder_up.startswith(name_up):
            return folder
        score = SequenceMatcher(None, name_up, folder_up).ratio()
        if score > best[0]:
            best = (score, folder)

    if best[0] >= FUZZY_THRESH and best[1]:
        return best[1]
    return None


def find_or_create_photo_folder(client_folder: Path, reference: str) -> Path:
    """Cherche rÃ©cursivement (dossiers seulement) un sous-dossier contenant la rÃ©fÃ©rence."""
    ref_up = reference.upper()
    for root, dirs, _ in walk(client_folder):
        for d in dirs:
            if ref_up in d.upper():
                return Path(root) / d
    new_folder = client_folder / f"{reference} PHOTOS"
    new_folder.mkdir(parents=True, exist_ok=True)
    print(f"  [+] Dossier crÃ©Ã© : {new_folder}")
    return new_folder


def find_subfolder_fuzzy(parent: Path, name: str) -> Path | None:
    """Cherche rÃ©cursivement dans parent un sous-dossier correspondant Ã  name."""
    name_up = name.upper().strip()
    best: tuple[float, Path | None] = (0.0, None)
    for root, dirs, _ in walk(parent):
        for d in dirs:
            d_up = d.upper()
            if name_up in d_up or d_up.startswith(name_up):
                return Path(root) / d
            score = SequenceMatcher(None, name_up, d_up).ratio()
            if score > best[0]:
                best = (score, Path(root) / d)
    if best[0] >= FUZZY_THRESH and best[1]:
        return best[1]
    return None


def find_folder_by_name(name: str) -> list[tuple[Path, Path]]:
    """Cherche dans toute l'arborescence (tous niveaux) un dossier par nom."""
    name_up = name.upper().strip()
    matches: list[tuple[Path, Path]] = []
    for client_folder in BASE_DIR.iterdir():
        if not client_folder.is_dir():
            continue
        if name_up in client_folder.name.upper():
            matches.append((client_folder, client_folder))
        for root, dirs, _ in walk(client_folder):
            for d in dirs:
                if name_up in d.upper():
                    matches.append((client_folder, Path(root) / d))
    return matches


def find_folder_by_ref(reference: str) -> list[tuple[Path, Path]]:
    """Scanne rÃ©cursivement (dossiers seulement) et retourne tous les (client_folder, sub)."""
    ref_up = reference.upper()
    matches = []
    for client_folder in BASE_DIR.iterdir():
        if not client_folder.is_dir():
            continue
        for root, dirs, _ in walk(client_folder):
            for d in dirs:
                if ref_up in d.upper():
                    matches.append((client_folder, Path(root) / d))
    return matches


# â”€â”€ Parsing du message â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

REF_RE = re.compile(r'\b(20\d{2}-\d+)\b')
LOT_RE = re.compile(r'\b(LOT\s*\d+\w*|BATIMENT\s+\w+|BT\s+\w+|BAT\s+\w+)\b', re.IGNORECASE)

_SKIP = {'RDV', 'J', 'M', 'S', 'AVANT', 'APRES', 'TRAVAUX', 'VENTE', 'ACHAT',
         'AMIANTE', 'PLOMB', 'DPE', 'TERMITE', 'PARASITE', 'GAZ', 'ELECTRICITE',
         'DIAGNOSTIC', 'MISSION', 'VISITE', 'RAPPORT'}


def parse_message(text: str) -> tuple[str | None, str | None, str | None, str | None]:
    """Retourne (client, reference, adresse, lot) depuis n'importe quel format.

    Format agenda : "RDV J - 2025-372 - AMIANTE AVANT TRAVAUX - DAUCHEZ - 1 VILLA SAINTE CROIX â€“ LOT 3..."
    """
    text = text.strip()

    ref_match = REF_RE.search(text)
    reference = ref_match.group(1) if ref_match else None

    normalized = re.sub(r'\s*[â€“â€”]\s*', ' - ', text)
    parts = [p.strip() for p in normalized.split(' - ') if p.strip()]

    client = None
    address = None
    lot = None

    if reference and len(parts) >= 2:
        ref_idx = next((i for i, p in enumerate(parts) if reference in p), -1)
        if ref_idx >= 0:
            for i, part in enumerate(parts[ref_idx + 1:], ref_idx + 1):
                part_up = part.strip().upper()
                if re.match(r'^\d', part_up):
                    if client:
                        address = part.strip()
                        remaining = ' '.join(parts[i:])
                        m = LOT_RE.search(remaining)
                        if m:
                            lot = m.group(1).upper()
                    break
                words = part_up.split()
                if any(w in _SKIP for w in words):
                    continue
                if 1 <= len(words) <= 3 and not client:
                    client = part_up

    if not client:
        normalized2 = re.sub(r'\s*[â€“â€”]\s*', ' - ', REF_RE.sub('', text))
        for part in re.split(r'[-/,;]', normalized2):
            part_up = part.strip().upper()
            if not part_up:
                continue
            if re.search(r'\d', part_up):
                continue
            words = part_up.split()
            if 1 <= len(words) <= 3 and not any(w in _SKIP for w in words):
                client = part_up
                break

    return (client or None, reference, address, lot)



def parse_direct_path(text: str) -> Path | None:
    """Retourne le Path si le texte est un chemin Windows valide vers un dossier existant."""
    t = text.strip().strip('"\'')
    if not re.match(r'^[A-Za-z]:\\', t):
        return None
    p = Path(t)
    return p if p.exists() and p.is_dir() else None


# â”€â”€ Telegram API â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def get_updates(bot: Bot) -> list:
    try:
        r = requests.get(
            f"{bot.tg_url}/getUpdates",
            params={"timeout": 30, "offset": bot.offset},
            timeout=35,
        )
        r.raise_for_status()
        return r.json().get("result", [])
    except requests.exceptions.Timeout:
        return []
    except Exception as e:
        print(f"[!] [{bot.name}] Erreur getUpdates: {e}")
        time.sleep(5)
        return []


def send_text(bot: Bot, chat_id: int, text: str):
    try:
        requests.post(
            f"{bot.tg_url}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=10,
        )
    except Exception as e:
        print(f"[!] [{bot.name}] Erreur envoi message: {e}")


def download_file(bot: Bot, file_id: str, dest: Path, default_ext: str = ".jpg") -> Path:
    r = requests.get(f"{bot.tg_url}/getFile", params={"file_id": file_id}, timeout=10)
    r.raise_for_status()
    file_path = r.json()["result"]["file_path"]
    ext = Path(file_path).suffix or default_ext

    resp = requests.get(f"{bot.tg_file_url}/{file_path}", timeout=60)
    resp.raise_for_status()

    final = dest.with_suffix(ext)
    final.write_bytes(resp.content)
    return final


# â”€â”€ Classification + extraction Claude Vision â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

CLASSIFY_PROMPT = """Tu es un assistant pour un diagnostiqueur immobilier franÃ§ais (amiante, plomb, DPE...).

Analyse cette image et dÃ©termine son type parmi trois catÃ©gories, puis extrait les informations correspondantes.

TYPES :
- "notes"    : feuille manuscrite de terrain (formulaire, relevÃ©s, croquis remplis Ã  la main)
- "pochette" : pochette ou enveloppe d'Ã©chantillon avec texte imprimÃ© (Parasits, RÃ©f commande, RÃ©f Ã©chantillon...)
- "autre"    : toute autre photo de terrain (matÃ©riau, local, installation, faÃ§ade...)

Retourne UNIQUEMENT un objet JSON selon le type dÃ©tectÃ© :

Si "notes" :
{"type": "notes", "texte": "<transcription complÃ¨te et fidÃ¨le de tout le texte visible, ligne par ligne>"}

Si "pochette" :
{"type": "pochette", "ref_commande": "<numÃ©ro de la rÃ©f commande, chiffres uniquement>", "ref_echantillon": "<ref Ã©chantillon si lisible, sinon chaine vide>"}

Si "autre" :
{"type": "autre", "nom": "<nom-descriptif-en-minuscules-tirets-max-4-mots-ascii>"}

RÃ©ponds uniquement avec le JSON brut, sans texte autour."""


def _call_vision(image_path: Path, prompt: str, max_tokens: int = 2048) -> str:
    return vision.call_vision(image_path, prompt, max_tokens=max_tokens)


def classify_photo(image_path: Path) -> dict:
    raw = _call_vision(image_path, CLASSIFY_PROMPT, max_tokens=2048)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"type": "autre", "nom": "photo-terrain"}


def save_notes_txt(texte: str, dest_folder: Path, image_stem: str) -> Path:
    out = dest_folder / f"{image_stem}_notes.txt"
    out.write_text(texte, encoding="utf-8")
    print(f"  [âœ“] Texte extrait -> {out}")
    return out


def rename_pochette(image_path: Path, ref_commande: str) -> Path:
    year = datetime.now().year
    ref_clean = re.sub(r'[^A-Za-z0-9]', '', ref_commande)
    name = f"{year}-{ref_clean} ECH"
    new_path = image_path.with_name(f"{name}{image_path.suffix}")
    counter = 1
    while new_path.exists() and new_path != image_path:
        new_path = image_path.with_name(f"{name}-{counter}{image_path.suffix}")
        counter += 1
    image_path.rename(new_path)
    return new_path


def rename_autre(image_path: Path, nom: str) -> Path:
    name = re.sub(r'[^a-z0-9-]', '-', nom.lower()).strip('-')
    name = re.sub(r'-+', '-', name) or "photo"
    new_path = image_path.with_name(f"{name}{image_path.suffix}")
    counter = 1
    while new_path.exists() and new_path != image_path:
        new_path = image_path.with_name(f"{name}-{counter}{image_path.suffix}")
        counter += 1
    image_path.rename(new_path)
    return new_path


# â”€â”€ Contexte par expÃ©diteur (propre Ã  chaque bot) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

OUI = {'oui', 'o', 'yes', 'y', '1', 'ok', 'correct', 'c\'est ca', 'c\'est Ã§a'}
NON = {'non', 'n', 'no', 'pas', 'faux', 'annuler', 'annule'}


def get_context(bot: Bot, user_id: int) -> dict | None:
    ctx = bot.pending.get(user_id)
    if ctx and (time.time() - ctx["ts"]) < CONTEXT_TTL:
        return ctx
    return None


def set_context(bot: Bot, user_id: int, client: str, ref: str, folder: Path):
    bot.pending[user_id] = {"client": client, "ref": ref, "folder": folder, "ts": time.time()}


def ask_confirm(bot: Bot, chat_id: int, user_id: int, client_folder: Path, ref: str, folder: Path):
    bot.confirming[user_id] = {
        "client_folder": client_folder,
        "ref": ref,
        "folder": folder,
        "ts": time.time(),
    }
    # Afficher le chemin relatif complet depuis le dossier client
    try:
        rel = folder.relative_to(client_folder)
        label = f"{client_folder.name} / {rel}"
    except ValueError:
        label = folder.name
    send_text(bot, chat_id, f"Dossier trouve :\n{label}\nC'est correct ? (oui / non)")


def check_confirm(bot: Bot, user_id: int) -> dict | None:
    ctx = bot.confirming.get(user_id)
    if ctx and (time.time() - ctx["ts"]) < CONTEXT_TTL:
        return ctx
    return None


def ask_select_subfolder(bot: Bot, chat_id: int, user_id: int, client_folder: Path):
    """Liste tous les sous-dossiers (rÃ©cursif) du client et demande de choisir."""
    subs = sorted([Path(root) / d
                   for root, dirs, _ in walk(client_folder)
                   for d in dirs])
    if not subs:
        ask_confirm(bot, chat_id, user_id, client_folder, "", client_folder)
        return

    bot.selecting[user_id] = {
        "client_folder": client_folder,
        "subfolders": subs,
        "ts": time.time(),
    }
    lines = [f"Client : {client_folder.name}\nChoisis un dossier :"]
    for i, s in enumerate(subs, 1):
        try:
            rel = s.relative_to(client_folder)
        except ValueError:
            rel = s.name
        lines.append(f"  {i}. {rel}")
    lines.append("Reponds avec le numero ou le nom.")
    send_text(bot, chat_id, "\n".join(lines))


def check_selecting(bot: Bot, user_id: int) -> dict | None:
    ctx = bot.selecting.get(user_id)
    if ctx and (time.time() - ctx["ts"]) < CONTEXT_TTL:
        return ctx
    return None


# â”€â”€ Traitement d'un update â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def handle_update(bot: Bot, update: dict):
    msg = update.get("message") or update.get("channel_post")
    if not msg:
        return

    chat_id  = msg["chat"]["id"]
    user_id  = msg.get("from", {}).get("id", chat_id)
    text     = msg.get("text", "") or ""
    caption  = msg.get("caption", "") or ""
    photos   = msg.get("photo")
    video    = msg.get("video")
    document = msg.get("document")
    voice    = msg.get("voice")    # message vocal enregistrÃ© dans Telegram (.ogg)
    audio    = msg.get("audio")    # fichier audio envoyÃ©

    # â”€â”€ RÃ©ponse texte (hors media) â”€â”€
    if text and not photos and not video and not document:
        reply = text.strip().lower()

        # 1. En attente de confirmation oui/non
        ctx_conf = check_confirm(bot, user_id)
        if ctx_conf:
            if reply in OUI:
                bot.confirming.pop(user_id, None)
                cf = ctx_conf["client_folder"]
                set_context(bot, user_id, cf.name, ctx_conf["ref"], ctx_conf["folder"])
                label = f"{cf.name}" + (f" / {ctx_conf['folder'].name}" if ctx_conf["ref"] else "")
                print(f"  [âœ“] [{bot.name}] Contexte confirmÃ© : {label}")
                send_text(bot, chat_id, f"OK ! Dossier : {label}\nEnvoie tes photos.")
            elif reply in NON:
                bot.confirming.pop(user_id, None)
                send_text(bot, chat_id, "AnnulÃ©. Renvoie le nom du dossier client.")
            else:
                send_text(bot, chat_id, "RÃ©ponds oui ou non.")
            return

        # 2. En attente de sÃ©lection de sous-dossier
        ctx_sel = check_selecting(bot, user_id)
        if ctx_sel:
            subs = ctx_sel["subfolders"]
            cf   = ctx_sel["client_folder"]
            chosen = None
            # SÃ©lection par numÃ©ro
            if text.strip().isdigit():
                idx = int(text.strip()) - 1
                if 0 <= idx < len(subs):
                    chosen = subs[idx]
            # SÃ©lection par nom (partiel, insensible Ã  la casse, chemin relatif inclus)
            if not chosen:
                t_up = text.strip().upper()
                for s in subs:
                    rel = str(s.relative_to(cf)).upper()
                    if t_up in rel or s.name.upper().startswith(t_up):
                        chosen = s
                        break
            if chosen:
                bot.selecting.pop(user_id, None)
                ask_confirm(bot, chat_id, user_id, cf, chosen.name, chosen)
            else:
                send_text(bot, chat_id, "Sous-dossier non trouvÃ©. RÃ©ponds avec le numÃ©ro ou le nom.")
            return

        # 3. Chemin Windows direct (ex: D:\Dropbox\...\INDIVISION DESBROSSE)
        direct = parse_direct_path(text)
        if direct is not None:
            try:
                rel_parts = direct.relative_to(BASE_DIR).parts
                client_folder = BASE_DIR / rel_parts[0] if rel_parts else direct
            except ValueError:
                client_folder = direct
            print(f"  [->] Chemin direct : {direct}")
            ask_confirm(bot, chat_id, user_id, client_folder, "", direct)
            return

        # 4. Parsing du message
        client, ref, address, lot = parse_message(text)
        print(f"  [->] [{bot.name}] Parsing : client='{client}' ref='{ref}' adresse='{address}' lot='{lot}'")

        # 5. Recherche par rÃ©fÃ©rence dans toute l'arborescence
        if ref:
            matches = find_folder_by_ref(ref)
            if len(matches) == 1:
                folder_client, folder = matches[0]
                ask_confirm(bot, chat_id, user_id, folder_client, ref, folder)
                return
            if len(matches) > 1:
                bot.selecting[user_id] = {
                    "client_folder": matches[0][0].parent,
                    "subfolders": [m[1] for m in matches],
                    "ts": time.time(),
                }
                lines = [f"Ref {ref} trouvÃ©e dans plusieurs dossiers :"]
                for i, (cf, sub) in enumerate(matches, 1):
                    lines.append(f"  {i}. {cf.name} / {sub.name}")
                lines.append("RÃ©ponds avec le numÃ©ro.")
                send_text(bot, chat_id, "\n".join(lines))
                return

        # 6. Recherche par nom client (premier niveau)
        folder_client = find_client_folder(client) if client else None
        if folder_client:
            if address:
                # Navigation hiÃ©rarchique : client â†’ adresse â†’ lot
                addr_folder = find_subfolder_fuzzy(folder_client, address)
                if addr_folder:
                    if lot:
                        lot_folder = find_subfolder_fuzzy(addr_folder, lot)
                        target = lot_folder if lot_folder else addr_folder
                    else:
                        target = addr_folder
                    ask_confirm(bot, chat_id, user_id, folder_client, ref or "", target)
                    return
                # Adresse non trouvÃ©e â†’ lister les sous-dossiers
                ask_select_subfolder(bot, chat_id, user_id, folder_client)
            elif ref:
                folder = find_or_create_photo_folder(folder_client, ref)
                ask_confirm(bot, chat_id, user_id, folder_client, ref, folder)
            else:
                ask_select_subfolder(bot, chat_id, user_id, folder_client)
            return

        # 7. Recherche par nom dans toute l'arborescence (sous-dossiers)
        search_term = client or (text.strip() if len(text.strip()) >= 4 else None)
        if search_term:
            matches = find_folder_by_name(search_term)
            if len(matches) == 1:
                cf, folder = matches[0]
                ask_confirm(bot, chat_id, user_id, cf, "", folder)
                return
            if len(matches) > 1:
                bot.selecting[user_id] = {
                    "client_folder": BASE_DIR,
                    "subfolders": [m[1] for m in matches],
                    "ts": time.time(),
                }
                lines = [f"Plusieurs dossiers pour '{search_term}' :"]
                for i, (cf, sub) in enumerate(matches, 1):
                    try:
                        rel = sub.relative_to(BASE_DIR)
                    except ValueError:
                        rel = sub
                    lines.append(f"  {i}. {rel}")
                lines.append("RÃ©ponds avec le numÃ©ro.")
                send_text(bot, chat_id, "\n".join(lines))
                return

        # Rien n'a matchÃ© : on rÃ©pond TOUJOURS (sinon le bot reste muet sur un faux dossier)
        recherche = client or ref or search_term or text.strip()
        print(f"  [?] [{bot.name}] Introuvable : '{recherche}'")
        send_text(bot, chat_id,
                  f"Dossier introuvable pour : {recherche}\n"
                  "VÃ©rifie le nom et rÃ©essaie, ou colle le chemin complet du dossier.")

    # â”€â”€ Fichiers : photo / vidÃ©o / document / audio â”€â”€
    elif photos or video or document or voice or audio:
        ctx = get_context(bot, user_id)

        if not ctx and caption:
            client, ref, address, lot = parse_message(caption)
            if client or ref:
                folder_client = find_client_folder(client) if client else None
                if folder_client:
                    folder = find_or_create_photo_folder(folder_client, ref) if ref else folder_client
                    set_context(bot, user_id, client or "", ref or "", folder)
                    ctx = get_context(bot, user_id)

        if not ctx:
            print(f"  [?] [{bot.name}] Fichier reÃ§u sans contexte de {user_id}")
            send_text(bot, chat_id, "Envoie d'abord le nom client + reference, puis les fichiers.")
            return

        dest_folder: Path = ctx["folder"]
        ref: str          = ctx["ref"]
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")

        if photos:
            file_id = photos[-1]["file_id"]
            tmp = dest_folder / f"TG-{ts}.jpg"
            saved = download_file(bot, file_id, tmp, ".jpg")
            kind = "Photo"
        elif video:
            file_id = video["file_id"]
            tmp = dest_folder / f"TG-{ts}.mp4"
            saved = download_file(bot, file_id, tmp, ".mp4")
            kind = "Video"
        elif document:
            file_id = document["file_id"]
            orig_name = document.get("file_name", f"TG-{ts}")
            tmp = dest_folder / orig_name
            saved = download_file(bot, file_id, tmp, Path(orig_name).suffix or ".bin")
            kind = "Fichier"
        elif voice:
            file_id = voice["file_id"]
            tmp = dest_folder / f"TG-{ts}.ogg"
            saved = download_file(bot, file_id, tmp, ".ogg")
            kind = "Audio"
        elif audio:
            file_id = audio["file_id"]
            orig_name = audio.get("file_name", f"TG-{ts}.mp3")
            tmp = dest_folder / orig_name
            saved = download_file(bot, file_id, tmp, Path(orig_name).suffix or ".mp3")
            kind = "Audio"
        else:
            return

        print(f"  [âœ“] {kind} sauvÃ©(e) : {saved}")

        if photos:
            print(f"  [->] Classification Claude Vision...")
            try:
                result = classify_photo(saved)
                ptype = result.get("type", "autre")
                print(f"  [->] Type : {ptype}")

                if ptype == "notes":
                    texte = result.get("texte", "")
                    txt = save_notes_txt(texte, dest_folder, saved.stem)
                    send_text(bot, chat_id, f"Notes extraites -> {txt.name}")

                elif ptype == "pochette":
                    ref_cmd = result.get("ref_commande", "").strip()
                    ref_ech = result.get("ref_echantillon", "").strip()
                    if ref_cmd:
                        renamed = rename_pochette(saved, ref_cmd)
                        print(f"  [->] RenommÃ© : {renamed.name}")
                        msg = f"Echantillon : {renamed.name}"
                        if ref_ech:
                            msg += f"\nRef ech : {ref_ech}"
                        send_text(bot, chat_id, msg)
                    else:
                        send_text(bot, chat_id, f"Pochette sauvee (ref commande illisible) : {saved.name}")

                else:
                    nom = result.get("nom", "photo")
                    renamed = rename_autre(saved, nom)
                    print(f"  [->] RenommÃ© : {renamed.name}")
                    send_text(bot, chat_id, f"Photo : {renamed.name}")

            except Exception as e:
                print(f"  [!] Erreur classification: {e}")
                send_text(bot, chat_id, f"Photo sauvee dans {dest_folder.name}")

        elif video:
            send_text(bot, chat_id, f"Video sauvee dans {dest_folder.name}")

        else:
            send_text(bot, chat_id, f"{kind} sauvÃ©(e) dans {dest_folder.name}")


# â”€â”€ Boucle principale â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def run_bot(bot: Bot):
    """Boucle de polling d'un seul bot (Ã  lancer dans son propre thread)."""
    print(f"  [{bot.name}] dÃ©marrÃ©, en attente de messages...")
    while True:
        updates = get_updates(bot)
        for update in updates:
            bot.offset = update["update_id"] + 1
            try:
                handle_update(bot, update)
            except Exception as e:
                print(f"[!] [{bot.name}] Erreur traitement update {update.get('update_id')}: {e}")


def main():
    print("=" * 50)
    print("  Bot Telegram - Classement photos terrain")
    print(f"  Dossier base : {BASE_DIR}")
    print("=" * 50)

    bots = load_bots()
    if not bots:
        print("[ERREUR] Aucun token : renseigne TELEGRAM_BOT_TOKEN dans .env")
        return
    if not OPENAI_KEY:
        print("[ERREUR] OPEN_IA manquant dans .env")
        return
    if not BASE_DIR.exists():
        print(f"[ERREUR] Dossier introuvable : {BASE_DIR}")
        return

    print(f"{len(bots)} bot(s) configurÃ©(s) : {', '.join(b.name for b in bots)}\n")

    import threading
    threads = []
    for bot in bots:
        t = threading.Thread(target=run_bot, args=(bot,), daemon=True, name=bot.name)
        t.start()
        threads.append(t)

    # Garde le process vivant tant que les threads tournent
    try:
        while any(t.is_alive() for t in threads):
            for t in threads:
                t.join(timeout=1)
    except KeyboardInterrupt:
        print("\nArrÃªt demandÃ© (Ctrl+C).")


if __name__ == "__main__":
    main()

