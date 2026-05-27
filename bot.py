from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any

from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from windiag_core import (
    Dossier,
    Room,
    format_recap,
    normalize_optional,
    parse_number,
    parse_surface,
    save_json,
)


logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
LOGGER = logging.getLogger("windiag-bot")


DOSSIER, ROOM_NAME, FLOOR, WALLS, CEILING, HEIGHT, ORIENTATION, JOINERY, NEXT_ACTION = range(9)

NEXT_KEYBOARD = ReplyKeyboardMarkup(
    [["Ajouter une pièce", "Terminer"], ["Annuler"]],
    resize_keyboard=True,
    one_time_keyboard=True,
)


def allowed_chat_ids() -> set[int]:
    raw = os.getenv("TELEGRAM_ALLOWED_CHAT_IDS", "").strip()
    if not raw:
        return set()
    return {int(item.strip()) for item in raw.split(",") if item.strip()}


def is_authorized(update: Update) -> bool:
    allowed = allowed_chat_ids()
    chat = update.effective_chat
    return bool(chat) and (not allowed or chat.id in allowed)


async def reject_if_needed(update: Update) -> bool:
    if is_authorized(update):
        return False
    if update.message:
        await update.message.reply_text("Accès non autorisé.")
    return True


def current_dossier(context: ContextTypes.DEFAULT_TYPE) -> Dossier:
    dossier = context.user_data.get("dossier")
    if not isinstance(dossier, Dossier):
        raise RuntimeError("No active dossier in conversation context")
    return dossier


def current_room(context: ContextTypes.DEFAULT_TYPE) -> dict[str, Any]:
    room = context.user_data.setdefault("room", {})
    if not isinstance(room, dict):
        room = {}
        context.user_data["room"] = room
    return room


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if await reject_if_needed(update):
        return ConversationHandler.END

    context.user_data.clear()
    await update.message.reply_text(
        "Nouveau relevé WinDiag.\n\nNom du logement ou du dossier ?",
        reply_markup=ReplyKeyboardRemove(),
    )
    return DOSSIER


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await reject_if_needed(update):
        return
    await update.message.reply_text(
        "Commande principale : /start\n"
        "Tu peux saisir une surface seule, par exemple `12.5`, ou avec matériau, par exemple `12,5 parquet`.",
        parse_mode="Markdown",
    )


async def dossier_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = update.message.text.strip()
    if not name:
        await update.message.reply_text("Il me faut un nom de dossier.")
        return DOSSIER

    context.user_data["dossier"] = Dossier(
        name=name,
        created_at=datetime.now().isoformat(timespec="seconds"),
    )
    await update.message.reply_text("Nom de la première pièce ?")
    return ROOM_NAME


async def room_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = update.message.text.strip()
    if not name:
        await update.message.reply_text("Nom de pièce vide. Exemple : Salon, Chambre 1, Cuisine.")
        return ROOM_NAME

    context.user_data["room"] = {"name": name}
    await update.message.reply_text("Sol : surface en m², avec matériau si utile. Exemple : `18,4 parquet`", parse_mode="Markdown")
    return FLOOR


async def surface_step(update: Update, context: ContextTypes.DEFAULT_TYPE, key: str, next_state: int, prompt: str) -> int:
    surface = parse_surface(update.message.text)
    if surface is None:
        await update.message.reply_text("Je n'ai pas trouvé de surface. Exemple : `12,5 béton`", parse_mode="Markdown")
        return {
            "floor": FLOOR,
            "walls": WALLS,
            "ceiling": CEILING,
        }[key]

    current_room(context)[key] = surface
    await update.message.reply_text(prompt, parse_mode="Markdown")
    return next_state


async def floor(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await surface_step(
        update,
        context,
        "floor",
        WALLS,
        "Murs : surface totale en m², avec matériau si utile. Exemple : `42 placo`",
    )


async def walls(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await surface_step(
        update,
        context,
        "walls",
        CEILING,
        "Plafond : surface en m², avec matériau si utile. Exemple : `18,4 peinture`",
    )


async def ceiling(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await surface_step(
        update,
        context,
        "ceiling",
        HEIGHT,
        "Hauteur sous plafond en m, ou `non`.",
    )


async def height(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    optional = normalize_optional(update.message.text)
    if optional is not None:
        value = parse_number(optional)
        if value is None:
            await update.message.reply_text("Hauteur non reconnue. Exemple : `2,50`, ou `non`.", parse_mode="Markdown")
            return HEIGHT
        current_room(context)["height_m"] = value
    else:
        current_room(context)["height_m"] = None

    await update.message.reply_text("Orientation, ou `non`. Exemple : Sud-Ouest", parse_mode="Markdown")
    return ORIENTATION


async def orientation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    current_room(context)["orientation"] = normalize_optional(update.message.text)
    await update.message.reply_text("Menuiseries, ou `non`. Exemple : 2 fenêtres PVC double vitrage", parse_mode="Markdown")
    return JOINERY


async def joinery(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    room_data = current_room(context)
    room_data["joinery"] = normalize_optional(update.message.text)

    room = Room(**room_data)
    dossier = current_dossier(context)
    dossier.rooms.append(room)
    context.user_data.pop("room", None)

    await update.message.reply_text(
        f"Pièce ajoutée : {room.name}\n\nAjouter une autre pièce ou terminer ?",
        reply_markup=NEXT_KEYBOARD,
    )
    return NEXT_ACTION


async def next_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    action = update.message.text.strip().lower()
    if "ajouter" in action:
        await update.message.reply_text("Nom de la pièce suivante ?", reply_markup=ReplyKeyboardRemove())
        return ROOM_NAME
    if "terminer" in action:
        return await finish(update, context)
    if "annuler" in action:
        return await cancel(update, context)

    await update.message.reply_text("Choisis une action avec les boutons.", reply_markup=NEXT_KEYBOARD)
    return NEXT_ACTION


async def finish(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    dossier = current_dossier(context)
    if not dossier.rooms:
        await update.message.reply_text("Aucune pièce saisie. Nom de la première pièce ?", reply_markup=ReplyKeyboardRemove())
        return ROOM_NAME

    recap = format_recap(dossier)
    json_path = save_json(dossier)

    await update.message.reply_text(recap, reply_markup=ReplyKeyboardRemove())
    with json_path.open("rb") as document:
        await update.message.reply_document(
            document=document,
            filename=json_path.name,
            caption="JSON du dossier pour WinDiag.",
        )
    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("Saisie annulée.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def build_application() -> Application:
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is missing. Copy .env.example to .env and fill it.")

    app = Application.builder().token(token).build()
    conversation = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            DOSSIER: [MessageHandler(filters.TEXT & ~filters.COMMAND, dossier_name)],
            ROOM_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, room_name)],
            FLOOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, floor)],
            WALLS: [MessageHandler(filters.TEXT & ~filters.COMMAND, walls)],
            CEILING: [MessageHandler(filters.TEXT & ~filters.COMMAND, ceiling)],
            HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, height)],
            ORIENTATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, orientation)],
            JOINERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, joinery)],
            NEXT_ACTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, next_action)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conversation)
    app.add_handler(CommandHandler("help", help_command))
    return app


def main() -> None:
    app = build_application()
    LOGGER.info("WinDiag bot started")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
