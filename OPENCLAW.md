# 📖 OPENCLAW — Référence complète du projet

> Document de référence pour **comprendre, configurer et dépanner** OpenClaw rapidement.
> Dernière mise à jour : **2026-06-04**

---

## 1. C'est quoi OpenClaw ?

OpenClaw est un **agent IA personnel auto-hébergé** qui tourne en local sur la machine.
Il expose :

- Un **gateway WebSocket** (port `18789`) avec un **dashboard web** : http://127.0.0.1:18789/
- Des **canaux** de discussion (Telegram, webchat…)
- Des **plugins** (OpenAI, Codex, mémoire, voix, contrôle téléphone, navigateur…)
- Un **workspace** d'agent (fichiers `.md` qui définissent son identité et son comportement)

Le modèle IA par défaut est **`openai/gpt-4o`** (clé OpenAI requise).

---

## 2. Arborescence de la config

Tout vit dans **`C:\Users\Assistante\.openclaw\`** :

| Élément | Rôle |
|---------|------|
| `openclaw.json` | **Config principale** (gateway, canaux, modèles, plugins, auth) |
| `openclaw.json.bak` / `.last-good` | Sauvegardes auto de la config |
| `.env` | **Secrets** : clés API, tokens, identifiants mail |
| `google-calendar-oauth.json` | Identifiants OAuth Google Calendar |
| `workspace/` | Cerveau de l'agent : `AGENTS.md`, `SOUL.md`, `IDENTITY.md`, `USER.md`, `TOOLS.md`, `BOOTSTRAP.md`, `HEARTBEAT.md` |
| `agents/main/agent/auth-profiles.json` | Profils d'authentification des providers |
| `plugins/` `plugin-skills/` `plugin-state/` | Plugins installés et leur état |
| `logs/` | Journaux (dont `logs/stability/` pour les crashs au démarrage) |
| `devices/` `identity/` | Appairage d'appareils et identité du gateway |

Logs runtime : `C:\Users\ASSIST~1\AppData\Local\Temp\openclaw\openclaw-AAAA-MM-JJ.log`

---

## 3. Où sont les exécutables (PATH)

⚠️ **`node`, `npm` et `openclaw` ne sont PAS dans le PATH** des sessions par défaut.
Chemins réels :

| Outil | Chemin |
|-------|--------|
| Node.js | `C:\Program Files\nodejs\node.exe` |
| npm | `C:\Program Files\nodejs\npm.cmd` |
| openclaw (CLI) | `C:\Users\Assistante\AppData\Roaming\npm\openclaw.cmd` |
| openclaw (module) | `…\AppData\Roaming\npm\node_modules\openclaw\openclaw.mjs` |

**Pour utiliser openclaw dans PowerShell**, ajouter d'abord au PATH :

```powershell
$env:Path += ";C:\Program Files\nodejs;$env:APPDATA\npm"
openclaw gateway status
```

---

## 4. Configuration actuelle (`openclaw.json`)

```jsonc
{
  "agents": {
    "defaults": {
      "workspace": "C:\\Users\\Assistante\\.openclaw\\workspace",
      "models": {
        "openai/gpt-5.5": { "alias": "GPT" },
        "openai/gpt-4o": {},
        "ollama/minimax-m3:cloud": {}
      },
      "model": { "primary": "ollama/minimax-m3:cloud" }   // ← modèle ACTIF (Ollama Cloud)
    }
  },
  "gateway": {
    "mode": "local",
    "auth": { "mode": "token", "token": "56ea7db2…6477" },
    "port": 18789,
    "bind": "loopback"          // accessible uniquement en local (127.0.0.1)
  },
  "plugins": { "entries": { "openai": {...}, "codex": {...}, "ollama": {...} } },
  "auth": {
    "profiles": {
      "openai:default": { "provider": "openai", "mode": "api_key" },
      "ollama:default": { "provider": "ollama", "mode": "api_key" }
    }
  },
  "channels": {
    "telegram": {
      "enabled": true,
      "botToken": "8671337423:…"   // ← LE bot actif (bot 2 = @Veilleregle_bot)
    }
  }
}
```

---

## 5. Les bots Telegram (point de confusion fréquent)

Il existe **2 tokens** historiques :

| Nom | Token | Bot | Utilisé ? |
|-----|-------|-----|-----------|
| **Bot 2** | `8671337423:…` | **@Veilleregle_bot** | ✅ **Oui, actif** |
| Bot 1 | ancien token | @DIAGNOSTIQUE_bot | ❌ Non (réserve, ne pas utiliser) |

> 🔁 **Changer de bot ne casse rien** : agenda (gog), mail (himalaya), modèle, identité et
> l'autorisation (`allowFrom` = ton **ID Telegram**, pas le bot) restent intacts. Il suffit
> de remplacer `botToken` dans `openclaw.json` + redémarrer. Le nouveau bot n'a pas d'historique
> → pas besoin de `/new`, parle-lui directement.

### 🔑 Règle d'or
**OpenClaw lit le token Telegram depuis `openclaw.json` → `channels.telegram.botToken`,
PAS depuis la variable `TELEGRAM_BOT_TOKEN` du `.env`.**

Le `.env` garde la variable par cohérence, mais c'est `openclaw.json` qui fait foi.
Pour **changer de bot** : modifier `botToken` dans `openclaw.json` puis **redémarrer le gateway**.

---

## 6. Le fichier `.env` (secrets)

```env
# Mail IONOS (entrant)
EMAIL_IMAP_SERVER=imap.ionos.fr
EMAIL_IMAP_PORT=993
EMAIL_IMAP_USER=contact@parasitis.fr
EMAIL_IMAP_PASSWORD=********

# Mail IONOS (sortant)
EMAIL_SMTP_SERVER=smtp.ionos.fr
EMAIL_SMTP_PORT=465
EMAIL_SMTP_USER=contact@parasitis.fr
EMAIL_SMTP_PASSWORD=********
EMAIL_FROM_ADDRESS=contact@parasitis.fr

# Telegram (par cohérence — non lu pour le canal, voir §5)
TELEGRAM_BOT_TOKEN=8671337423:…

# OpenAI — DEUX noms : OPEN_IA (autre projet) + OPENAI_API_KEY (requis par openclaw)
OPEN_IA=sk-proj-…
OPENAI_API_KEY=sk-proj-…

# Ollama — "ollama-local" (n'importe quelle valeur) ; le serveur local gère l'auth cloud
OLLAMA_API_KEY=ollama-local
```

### ⚠️ Piège n°1 — le nom de la clé OpenAI
OpenClaw exige **`OPENAI_API_KEY`**. Si seule `OPEN_IA` est présente, le gateway
**refuse de démarrer** avec :

```
[SECRETS_RELOADER_DEGRADED] Environment variable "OPENAI_API_KEY" is missing or empty.
Gateway failed to start: required secrets are unavailable.
```

➡️ **Fix** : ajouter une ligne `OPENAI_API_KEY=<la clé>` dans `.env`, puis redémarrer.

---

## 7. Commandes essentielles

> Préfixer chaque session par : `$env:Path += ";C:\Program Files\nodejs;$env:APPDATA\npm"`

| Action | Commande |
|--------|----------|
| Statut du gateway | `openclaw gateway status` |
| Diagnostic complet | `openclaw gateway status --deep` |
| Démarrer (foreground) | `openclaw gateway run` |
| Démarrer en libérant le port | `openclaw gateway run --force --bind loopback` |
| Arrêter | `openclaw gateway stop` |
| Diagnostics de stabilité | `openclaw gateway stability` |
| Coût d'utilisation | `openclaw gateway usage-cost` |
| Aide | `openclaw gateway --help` |

### Redémarrage propre (procédure recommandée)

```powershell
$env:Path += ";C:\Program Files\nodejs;$env:APPDATA\npm"
openclaw gateway stop
openclaw gateway run --force --bind loopback   # --force tue tout listener résiduel sur 18789
```

Le gateway tourne en **foreground** : le lancer dans une fenêtre/tâche dédiée
(ou en arrière-plan). Il n'est **pas** installé comme service Windows
(`Service: Scheduled Task (missing)` est normal).

---

## 8. Vérifier que tout marche

Au démarrage réussi, le log doit afficher :

```
[gateway] ready
[telegram] [default] starting provider (@Veilleregle_bot)
[gateway] agent model: ollama/minimax-m3:cloud
[gateway] http server listening (11 plugins: …, ollama, openai, telegram; …)
```

Puis tester :
- **Dashboard** : ouvrir http://127.0.0.1:18789/
- **Telegram** : écrire à **@Veilleregle_bot**
- **Inférence directe** (sans passer par un canal) :
  ```powershell
  openclaw infer model run --model "ollama/minimax-m3:cloud" --prompt "capitale de la France?"
  # → doit répondre "Paris"
  ```

---

## 9. Dépannage (les pannes déjà rencontrées)

| Symptôme | Cause | Fix |
|----------|-------|-----|
| `Could not free port 18789 … TIME_WAIT or kernel hold` | Ancien listener pas libéré / autre process (ex `bot_telegram.py`) sur le port | Relancer avec `--force`, ou tuer le PID qui tient le port |
| `OPENAI_API_KEY is missing or empty` | Clé nommée `OPEN_IA` au lieu de `OPENAI_API_KEY` | Ajouter `OPENAI_API_KEY=` dans `.env` (§6) |
| `insufficient_quota` / 429 OpenAI | Crédit OpenAI épuisé ou clé invalide | Utiliser une clé OpenAI avec du crédit — **OU** basculer sur Ollama (§12) |
| `node`/`npm`/`openclaw` introuvable | Pas dans le PATH | Préfixer le PATH (§3) |
| Conflit 409 Telegram (`terminated by other getUpdates`) | Deux process interrogent le même bot (openclaw **+** `bot_telegram.py`) | Ne faire tourner qu'**un seul** consommateur par token Telegram |
| Mauvais bot répond | `botToken` dans `openclaw.json` ≠ bot voulu | Corriger `botToken` puis redémarrer (§5) |
| `401 Non autorisé` sur modèle `…:cloud` Ollama | Pas connecté à ollama.com | `ollama signin` → ouvrir le lien → valider (§12) |
| `Ollama requires authentication to be registered` | `OLLAMA_API_KEY` absent | Ajouter `OLLAMA_API_KEY=ollama-local` dans `.env` (§12) |
| `config patch … rejected (size-drop)` | Le `.env`/json a été reformaté (espaces) ; le patch CLI minifie → garde-fou anti-perte | Éditer `openclaw.json` directement (Edit), ou re-patcher après reformatage |

### Identifier qui occupe le port 18789

```powershell
Get-NetTCPConnection -LocalPort 18789 -ErrorAction SilentlyContinue |
  Select-Object State, OwningProcess
# puis : Get-Process -Id <PID>
```

---

## 10. Services externes — état d'intégration

| Service | État | Détails |
|---------|------|---------|
| **Ollama (`minimax-m3:cloud`)** | ✅ **Modèle ACTIF** | Provider local Ollama + cloud. C'est le modèle primaire actuel. Voir §12. |
| **OpenAI (gpt-4o / gpt-5.5)** | ⚠️ Dépend du crédit | Clé dans `.env` (`OPENAI_API_KEY`). Compte en `insufficient_quota` → conservé en secours. |
| **Telegram** | ✅ Actif | @Veilleregle_bot (bot 2) via `openclaw.json`. |
| **Google Agenda (`gog`)** | ✅ **Actif** | Binaire Windows natif installé + OAuth `contact@parasitis.com` autorisé (scope calendar). Voir §14. |
| **Mail IONOS (`himalaya`)** | ✅ **Actif** | Binaire Windows installé + config `contact@parasitis.com` (IONOS). Voir §15. |

> ℹ️ **`gog` ET `himalaya` fonctionnent en natif Windows** (binaires Go/Rust). Pas besoin de WSL/Docker.

---

## 11. Workspace de l'agent (`workspace/*.md`)

Ces fichiers définissent le comportement de l'agent (à éditer pour le personnaliser) :

| Fichier | Rôle |
|---------|------|
| `IDENTITY.md` | Qui est l'agent (nom, persona) |
| `SOUL.md` | Valeurs / ton / style |
| `USER.md` | Infos sur l'utilisateur humain (à remplir) |
| `TOOLS.md` | Notes spécifiques au setup local (appareils, hosts, voix TTS…) |
| `AGENTS.md` | Définition des agents |
| `BOOTSTRAP.md` | Instructions de démarrage |
| `HEARTBEAT.md` | Tâches récurrentes / battement de cœur |

---

## 12. Ollama — modèle IA actif (`minimax-m3:cloud`)

Pour contourner le `insufficient_quota` d'OpenAI, openclaw tourne sur **Ollama**.
Le modèle `minimax-m3:cloud` est un modèle **Ollama Cloud** (exécuté sur les serveurs
d'Ollama, pas en local), donc il faut être **connecté à ollama.com**.

### Emplacement Ollama
- Binaire : `C:\Users\Assistante\AppData\Local\Programs\Ollama\ollama.exe`
- Serveur (API) : `http://127.0.0.1:11434` (API compatible OpenAI sur `/v1`)

### Procédure d'installation complète (déjà faite)
```powershell
$ollama = "C:\Users\Assistante\AppData\Local\Programs\Ollama\ollama.exe"
& $ollama signin          # → ouvre un lien ollama.com/connect?... à valider dans le navigateur
& $ollama run minimax-m3:cloud "test"   # vérifie l'accès au modèle cloud
```

### Config openclaw pour Ollama (3 points)
1. **Plugin activé** dans `openclaw.json` → `plugins.entries.ollama.enabled = true`
   (+ `config.discovery.enabled = true`). Le plugin Ollama est **bundled** dans openclaw.
2. **Modèle déclaré + primaire** dans `agents.defaults` :
   ```jsonc
   "models": { "ollama/minimax-m3:cloud": {} },
   "model":  { "primary": "ollama/minimax-m3:cloud" }
   ```
3. **Auth** (2 fichiers + 1 env) :
   - `.env` → `OLLAMA_API_KEY=ollama-local`  *(n'importe quelle valeur ; signal "local")*
   - `agents/main/agent/auth-profiles.json` → profil `ollama:default` (api_key, env `OLLAMA_API_KEY`)
   - `openclaw.json` → `auth.profiles.ollama:default = { provider: "ollama", mode: "api_key" }`

### Vérifier
```powershell
openclaw models status            # → "ollama ... ollama:default=ref(env:OLLAMA_API_KEY)"
openclaw infer model run --model "ollama/minimax-m3:cloud" --prompt "capitale de la France?"
# → "Paris"
```

> ⚠️ **`config patch` rejeté (size-drop)** : si `openclaw.json` a été reformaté avec
> plein d'espaces, le patch CLI le minifie et un garde-fou bloque l'écriture.
> Solution : éditer le JSON **directement** (à la main / Edit), c'est ce qui a été fait ici.

---

## 13. Checklist « ça remarche » (résumé express)

1. `$env:Path += ";C:\Program Files\nodejs;$env:APPDATA\npm"`
2. Serveur Ollama lancé + connecté : `ollama run minimax-m3:cloud "test"` répond
3. `.env` contient **`OLLAMA_API_KEY=ollama-local`** (et `OPENAI_API_KEY` pour le secours)
4. `openclaw.json` → `model.primary = "ollama/minimax-m3:cloud"` + plugin `ollama` activé
5. `openclaw.json` → `channels.telegram.botToken` = bot 2 (`8671337423:…`, @Veilleregle_bot)
6. `openclaw gateway stop` puis `openclaw gateway run --force --bind loopback`
7. Log = `[gateway] ready` + `(@Veilleregle_bot)` + `agent model: ollama/minimax-m3:cloud`
8. Tester : `openclaw infer model run …` → "Paris", puis Telegram @Veilleregle_bot

---

## 14. Google Agenda via `gog` (Google Workspace CLI)

Le bot lit l'agenda Google grâce au skill **`gog`** (bundlé dans openclaw). Contrairement
à ce qu'on croyait, **`gog` a un binaire Windows natif** (c'est un binaire Go).

### Installation (déjà faite)
- **Binaire** : `C:\Users\Assistante\AppData\Roaming\npm\gog.exe` (v0.21.0)
  - Source : releases GitHub `steipete/gogcli` → `gogcli_X_windows_amd64.zip`
  - ⚠️ Un ancien **shim npm cassé** (`gog.cmd` + `gog`) pointait vers un paquet absent
    (`node_modules\gog`) → erreur « chemin introuvable ». **Supprimés** et remplacés par `gog.exe`.
- **Config gog** : `C:\Users\Assistante\AppData\Roaming\gogcli\` (config.json, credentials.json, tokens)

### Authentification Google (OAuth)
```powershell
$gog = "C:\Users\Assistante\AppData\Roaming\npm\gog.exe"
# 1. Enregistrer le client OAuth (le JSON client_secret de Google Cloud)
& $gog auth credentials set "C:\...\client_secret_....json"
# 2. Autoriser le compte (flux navigateur, scope calendar uniquement)
& $gog auth add contact@parasitis.com --services calendar --timeout 10m
# 3. Vérifier
& $gog auth list
& $gog -a contact@parasitis.com calendar calendars        # liste les agendas
& $gog -a contact@parasitis.com calendar events --all --max 15
```

### Compte autorisé
- **contact@parasitis.com** (Google Workspace) — scope **calendar**
- Agendas visibles : PARASITIS S.A.S, Eva ROLLET, Joel CHICHE, Frédérique VALETTE, etc.

### ⚠️ Pièges OAuth rencontrés (côté Google Cloud, projet `amiable-crane-498408-j8`)
| Erreur | Cause | Fix |
|--------|-------|-----|
| `403 access_denied` — « app en test, testeurs approuvés uniquement » | App OAuth en mode **Testing**, compte pas testeur | Console → OAuth consent → **Test users** → ajouter `contact@parasitis.com` |
| `400 invalid_scope` sur `calendar` | **API Google Calendar pas activée** dans le projet | Activer **Google Calendar API** dans la console |
| `context deadline exceeded` | Flux OAuth pas terminé à temps / scopes trop larges | Limiter `--services calendar` + augmenter `--timeout` |
| Trop de scopes (consent énorme) | gog demande tout par défaut | Toujours passer **`--services calendar`** |

### 🐞 Bug clé : le modèle ne lisait pas le skill (et hallucinait)
Symptôme : le bot répondait « il me faut le client_secret.json / l'auth n'est pas faite »
alors que tout était configuré. Le modèle **appelait bien l'outil `read`** mais sur le
**mauvais chemin** :
```
[tools] read failed: ENOENT: C:\Users\Assistante\.openclaw\skills\gog\SKILL.md
```
Le skill `gog` n'existait que dans le dossier **bundlé** (`...\npm\node_modules\openclaw\skills\gog\`),
pas dans le dossier **managed** (`.openclaw\skills\`) que le modèle interrogeait. Faute de lire
les instructions, il retombait sur le texte générique « Setup (once) » → hallucination.

**Fix appliqué :**
1. Copier `SKILL.md` dans `C:\Users\Assistante\.openclaw\skills\gog\SKILL.md`.
2. Éditer cette copie pour indiquer **« SETUP DÉJÀ FAIT »** + le compte `contact@parasitis.com`
   + les commandes `gog calendar` prêtes à l'emploi (sinon la section « Setup (once) »
   d'origine relance la confusion).
3. Redémarrer le gateway.

> 💡 Le tool-calling **fonctionne** avec `qwen3-coder:480b-cloud` via Ollama (le modèle
> appelait `read` et `exec`). Le blocage venait du **contenu/chemin du skill**, pas du modèle.

### Bon à savoir
- Un seul compte autorisé → gog l'utilise par défaut, mais on peut forcer avec `-a contact@parasitis.com`.
- Pour un accès **sans login interactif** (token qui n'expire jamais), alternative = **compte de service Workspace** avec délégation domaine (nécessite admin Workspace).
- Le skill `gog` couvre aussi Gmail, Drive, Contacts, Tasks, Sheets, Docs… (activer les API correspondantes + scopes au besoin).

---

## 15. Mail IONOS via `himalaya`

Le bot lit/écrit les mails via le skill **`himalaya`** (CLI Rust, binaire Windows natif).

### ⚠️ Le piège des adresses (résolu)
- Mail réel = **`contact@parasitis.com`** hébergé chez **IONOS** (webmail).
- `contact@parasitis.com` est AUSSI un **compte Google** (pour l'agenda) — créé avec cette
  adresse externe, mais le **mail** reste sur IONOS. Même adresse, deux services distincts.
- ❌ `contact@parasitis.fr` n'existe pas (bounce + auth refusée). Ne pas l'utiliser.
- Config IMAP/SMTP qui marche : serveur **imap.ionos.fr / smtp.ionos.fr**, login = **l'adresse .com**.

### Installation (déjà faite)
- Binaire : `C:\Users\Assistante\AppData\Roaming\npm\himalaya.exe` (v1.2.0)
  - Source : releases GitHub `pimalaya/himalaya` → `himalaya.x86_64-windows.zip`
- Config : `C:\Users\Assistante\AppData\Roaming\himalaya\config.toml`
  - account `parasitis` : IMAP imap.ionos.fr:993 (tls), SMTP smtp.ionos.fr:465 (tls), login contact@parasitis.com

### Commandes
```
himalaya envelope list --folder INBOX --page-size 10
himalaya message read <id>
himalaya envelope list from client@x.com
himalaya message reply <id>
```

### ⚠️ Pièges Windows
| Problème | Cause | Fix |
|----------|-------|-----|
| `Cannot find configuration at C.` | himalaya découpe les chemins sur `:` → casse `C:\...` | **Ne pas** passer `--config` ; laisser la config par défaut (`%APPDATA%\himalaya`) |
| Wizard interactif (`configure? Y/n`) | config introuvable / commande mal lancée | S'assurer que `config.toml` est dans `%APPDATA%\himalaya\`, ne jamais lancer `account configure` |
| Identifiants refusés | mauvaise adresse (`.fr`) | login = `contact@parasitis.com` |

### Skill openclaw
- Copié dans `C:\Users\Assistante\.openclaw\skills\himalaya\` (+ `references/`), SKILL.md adapté
  « setup fait, pas de --config, pas de wizard ».
- Capacité rappelée dans `workspace/USER.md` et `workspace/TOOLS.md`.
