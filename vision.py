"""
Lecture d'images via OpenAI (gpt-4o).

Fournit une fonction unique `call_vision(image_path, prompt)` qui envoie une
image + une consigne au modèle et renvoie le texte produit.

Configuration via .env :
  OPEN_IA        clé OpenAI (format sk-proj... ou sk-...)
  OPENAI_MODEL   optionnel, défaut "gpt-4o"
"""

import base64
import os
from pathlib import Path

from openai import OpenAI

OPENAI_KEY   = os.getenv("OPEN_IA", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

_MEDIA = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png"}


def call_vision(image_path: Path, prompt: str, max_tokens: int = 2048,
                json_output: bool = True) -> str:
    """Envoie l'image et la consigne à OpenAI, renvoie le texte de la réponse.

    json_output=True force une sortie JSON (response_format json_object), ce qui
    rend json.loads(...) fiable côté appelant. Le prompt doit mentionner "json".
    """
    if not OPENAI_KEY:
        raise RuntimeError("OPEN_IA manquant dans .env")

    client = OpenAI(api_key=OPENAI_KEY)
    media = _MEDIA.get(image_path.suffix.lower().lstrip('.'), "image/jpeg")
    b64 = base64.b64encode(image_path.read_bytes()).decode()

    kwargs = {}
    if json_output:
        kwargs["response_format"] = {"type": "json_object"}

    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url",
             "image_url": {"url": f"data:{media};base64,{b64}"}},
        ]}],
        **kwargs,
    )
    return (resp.choices[0].message.content or "").strip()
