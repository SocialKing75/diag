---
name: parasitis-vps-contact-form
description: Setup du formulaire de contact du site parasitis.fr (VPS Django, envoi email)
metadata:
  type: project
---

Le site **parasitis.fr** est une app **Django** déployée sur un VPS dans `/var/www/parasitis-deploy/` (app `landing`, projet `parasitis`, venv local, service systemd `parasitis.service` derrière nginx via `parasitis.sock`). Accès SSH.

**Formulaire de contact** (page `/contact/`, template `landing/templates/contact.html`, JS poste vers `/api/contact/` → vue `contact_form`). La vue appelle `_send_contact_email()` dans `landing/views.py`.

Envoi configuré en **Resend (prioritaire) + secours SMTP IONOS automatique** : si Resend échoue (ex. domaine non vérifié), bascule sur le backend SMTP Django IONOS. Variables dans `.env` du VPS + `parasitis/settings.py` : `RESEND_API_KEY`, `RESEND_FROM_EMAIL`, plus la config IONOS existante.

**Gotcha .fr / .com** : la vraie boîte mail IONOS qui reçoit est **`contact@parasitis.com`** (`EMAIL_HOST_USER`/`DEFAULT_FROM_EMAIL` sont en `.com`). La boîte `contact@parasitis.fr` **n'existe pas** → tout envoi vers `.fr` bounce en `550 mailbox unavailable`. `CONTACT_RECEIVER_EMAIL` a donc été corrigé en `contact@parasitis.com`.

**En attente** : domaine `parasitis.fr` à vérifier dans Resend (DNS DKIM/SPF sur sous-domaine `send.parasitis.fr` ajoutés chez IONOS). Tant que non « Verified », l'envoi passe par IONOS (secours). Une fois vérifié, Resend prend le relais tout seul. À envisager : vérifier `parasitis.com` dans Resend plutôt et mettre `RESEND_FROM_EMAIL=contact@parasitis.com` pour la cohérence.
