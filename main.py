"""
Marketing Analytics Bot
========================
• Meta Ads — kunlik hisobot (scheduler)
• AmoCRM   — webhook orqali real-time + kunlik hisobot
• FastAPI  — webhook server (Railway PORT da ishlaydi)
"""
import asyncio
import logging
import threading

import pytz
import uvicorn
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ParseMode

import config
import lead_store
import webhook_server
from meta_api import build_meta_report, format_meta_message
from lead_store import get_today_leads, analyze_leads, format_amo_message, reset_daily

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
log = logging.getLogger(__name__)
TZ = pytz.timezone(config.TIMEZONE)


# ─── Hisobot funksiyalari ────────────────────────────────────────────────────

async def send_meta_report(bot: Bot):
    try:
        report = build_meta_report()
        await bot.send_message(
            chat_id=config.TELEGRAM_GROUP_ID,
            text=format_meta_message(report),
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        log.error(f"Meta xato: {e}")
        await bot.send_message(
            chat_id=config.TELEGRAM_GROUP_ID,
            text=f"⚠️ Meta Ads xatosi:\n<code>{e}</code>",
            parse_mode=ParseMode.HTML,
        )


async def send_amo_report(bot: Bot):
    try:
        leads  = get_today_leads()
        report = analyze_leads(leads)
        await bot.send_message(
            chat_id=config.TELEGRAM_GROUP_ID,
            text=format_amo_message(report),
            parse_mode=ParseMode.HTML,
        )
        reset_daily()
    except Exception as e:
        log.error(f"AMO xato: {e}")
        await bot.send_message(
            chat_id=config.TELEGRAM_GROUP_ID,
            text=f"⚠️ AmoCRM xatosi:\n<code>{e}</code>",
            parse_mode=ParseMode.HTML,
        )


async def send_full_report(bot: Bot):
    from datetime import datetime
    now_str = datetime.now(TZ).strftime("%d.%m.%Y %H:%M")
    await bot.send_message(
        chat_id=config.TELEGRAM_GROUP_ID,
        text=f"🌅 <b>Kunlik hisobot</b> — {now_str}\n━━━━━━━━━━━━━━━━━━━━",
        parse_mode=ParseMode.HTML,
    )
    await send_meta_report(bot)
    await asyncio.sleep(1)
    await send_amo_report(bot)
    await bot.send_message(
        chat_id=config.TELEGRAM_GROUP_ID,
        text="✅ <b>Hisobot tugadi.</b>",
        parse_mode=ParseMode.HTML,
    )


# ─── Telegram buyruqlar ──────────────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 <b>Marketing Analytics Bot</b>\n\n"
        f"⏰ Hisobot vaqti: {config.REPORT_HOUR:02d}:{config.REPORT_MINUTE:02d} ({config.TIMEZONE})\n\n"
        "/hisobot — To'liq hisobot\n"
        "/meta    — Faqat Meta Ads\n"
        "/amo     — Faqat AmoCRM\n"
        "/webhook — Webhook URL ni ko'rish",
        parse_mode=ParseMode.HTML,
    )


async def cmd_hisobot(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Tayyorlanmoqda...")
    await send_full_report(ctx.bot)


async def cmd_meta(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Meta Ads...")
    await send_meta_report(ctx.bot)


async def cmd_amo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ AmoCRM...")
    await send_amo_report(ctx.bot)


async def cmd_webhook(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔗 <b>AmoCRM Webhook URL:</b>\n\n"
        "<code>https://YOUR-APP.up.railway.app/webhook/amo</code>\n\n"
        "Railway da deploy qilgandan keyin to'g'ri URL ko'rinadi.\n"
        "Bu URL ni AmoCRM → Sozlamalar → Webhook ga kiriting.",
        parse_mode=ParseMode.HTML,
    )


# ─── Scheduler ───────────────────────────────────────────────────────────────

def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=TZ)
    scheduler.add_job(
        send_full_report,
        trigger="cron",
        hour=config.REPORT_HOUR,
        minute=config.REPORT_MINUTE,
        args=[bot],
        id="daily_report",
        replace_existing=True,
    )
    log.info(f"Scheduler: har kuni {config.REPORT_HOUR:02d}:{config.REPORT_MINUTE:02d}")
    return scheduler


# ─── FastAPI webhook server (alohida threadda) ───────────────────────────────

def run_webhook_server():
    uvicorn.run(
        webhook_server.app,
        host="0.0.0.0",
        port=config.PORT,
        log_level="warning",
    )


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    # Telegram app
    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start",   cmd_start))
    app.add_handler(CommandHandler("hisobot", cmd_hisobot))
    app.add_handler(CommandHandler("meta",    cmd_meta))
    app.add_handler(CommandHandler("amo",     cmd_amo))
    app.add_handler(CommandHandler("webhook", cmd_webhook))

    # Webhook serverga bot ulash (real-time xabarlar uchun)
    webhook_server.set_bot(app.bot, config.TELEGRAM_GROUP_ID)

    # FastAPI ni alohida threadda ishga tushirish
    thread = threading.Thread(target=run_webhook_server, daemon=True)
    thread.start()
    log.info(f"Webhook server port {config.PORT} da ishga tushdi")

    # Scheduler
    scheduler = setup_scheduler(app.bot)
    scheduler.start()

    log.info("Bot ishga tushdi ✅")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
