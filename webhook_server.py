"""
FastAPI webhook server.
AmoCRM bu serverga POST so'rov yuboradi.
"""
import logging
from fastapi import FastAPI, Request

import lead_store

log = logging.getLogger(__name__)
app = FastAPI()

# Telegram botni keyinroq ulaymiz
_bot = None
_group_id = None


def set_bot(bot, group_id: int):
    global _bot, _group_id
    _bot = bot
    _group_id = group_id


@app.get("/")
async def health():
    return {"status": "ok", "message": "Marketing Bot webhook server ishlayapti ✅"}


@app.post("/webhook/amo")
async def amo_webhook(request: Request):
    """
    AmoCRM barcha hodisalar uchun shu URL ga POST yuboradi.
    Form-encoded format (application/x-www-form-urlencoded).
    """
    try:
        form = await request.form()
        data = dict(form)
        log.info(f"AmoCRM webhook keldi: {list(data.keys())[:5]}")

        lead = _parse_amo_event(data)

        if lead:
            lead_store.add_lead(lead)

            # Yangi lid kelsa — darhol Telegram ga xabar
            if lead.get("event") == "add" and _bot and _group_id:
                text = (
                    f"🆕 <b>Yangi lid!</b>\n"
                    f"👤 Ism: {lead.get('name', '—')}\n"
                    f"📊 Status: {lead.get('status', '—')}\n"
                    f"💰 Byudjet: {lead.get('price', '0')} so'm\n"
                    f"🏷 Manba: {lead.get('pipeline', '—')}"
                )
                await _bot.send_message(
                    chat_id=_group_id,
                    text=text,
                    parse_mode="HTML",
                )

        return {"ok": True}

    except Exception as e:
        log.error(f"Webhook xatosi: {e}")
        return {"ok": False, "error": str(e)}


def _parse_amo_event(data: dict) -> dict | None:
    """Form data dan lid ma'lumotlarini oladi."""

    # AmoCRM leads[add][0][name] formatida yuboradi
    event_type = None
    lead_data  = {}

    for key, val in data.items():
        # leads[add][0][name] → event=add, field=name
        if key.startswith("leads["):
            parts = key.replace("]", "").split("[")
            # parts = ['leads', 'add', '0', 'name']
            if len(parts) >= 4:
                event_type          = parts[1]
                field               = parts[3]
                lead_data[field]    = val

    if not lead_data:
        return None

    # Status matnini aniqlash
    status_id = lead_data.get("status_id", "")
    is_won    = status_id == "142"
    is_lost   = status_id == "143"

    return {
        "event":    event_type or "update",
        "name":     lead_data.get("name", "Nomsiz"),
        "price":    lead_data.get("price", "0"),
        "status":   lead_data.get("status_name") or _status_label(status_id),
        "pipeline": lead_data.get("pipeline_name", "—"),
        "is_won":   is_won,
        "is_lost":  is_lost,
    }


def _status_label(status_id: str) -> str:
    labels = {
        "142": "✅ Yutildi",
        "143": "❌ Yutqazildi",
    }
    return labels.get(status_id, f"Status #{status_id}")
