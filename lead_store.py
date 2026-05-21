"""
Kunlik lidlarni xotirada saqlaydi.
Webhook orqali kelgan ma'lumotlar shu yerda yig'iladi.
"""
from datetime import datetime
from collections import defaultdict

# Barcha bugungi lidlar
_leads: list[dict] = []


def add_lead(lead: dict):
    """Yangi lid qo'shadi."""
    lead["received_at"] = datetime.now().isoformat()
    _leads.append(lead)


def get_today_leads() -> list[dict]:
    """Bugungi lidlarni qaytaradi."""
    today = datetime.now().date().isoformat()
    return [l for l in _leads if l.get("received_at", "").startswith(today)]


def reset_daily():
    """Har kuni hisobotdan keyin tozalaydi."""
    today = datetime.now().date().isoformat()
    global _leads
    _leads = [l for l in _leads if not l.get("received_at", "").startswith(today)]


def analyze_leads(leads: list[dict]) -> dict:
    """Lidlarni tahlil qiladi."""
    total = len(leads)
    status_counts: dict[str, int] = defaultdict(int)
    contacted = 0
    not_contacted = 0
    won = 0
    lost = 0

    for lead in leads:
        status = lead.get("status", "Yangi")
        status_counts[status] += 1

        event = lead.get("event", "")
        if event == "add":
            not_contacted += 1
        elif event in ("update", "status"):
            contacted += 1

        if lead.get("is_won"):
            won += 1
        elif lead.get("is_lost"):
            lost += 1

    in_progress = total - won - lost
    conversion  = round(won / total * 100, 1) if total > 0 else 0.0

    return {
        "date":          datetime.now().strftime("%d.%m.%Y"),
        "total":         total,
        "contacted":     contacted,
        "not_contacted": not_contacted,
        "won":           won,
        "lost":          lost,
        "in_progress":   in_progress,
        "conversion":    conversion,
        "status_counts": dict(status_counts),
    }


def format_amo_message(report: dict) -> str:
    lines = [
        f"🗂 <b>AMO CRM HISOBOT</b> — {report['date']}",
        "━━━━━━━━━━━━━━━━━━━━",
        f"📥 Jami lidlar: <b>{report['total']}</b>",
        f"✅ Bog'lanildi: <b>{report['contacted']}</b>",
        f"❌ Bog'lanilmadi: <b>{report['not_contacted']}</b>",
        "",
        f"🏆 Yutildi (won): <b>{report['won']}</b>",
        f"💔 Yutqazildi: <b>{report['lost']}</b>",
        f"⏳ Jarayonda: <b>{report['in_progress']}</b>",
        f"📈 Konversiya: <b>{report['conversion']}%</b>",
        "",
        "📋 <b>Statuslar:</b>",
    ]
    for status, count in sorted(report["status_counts"].items(), key=lambda x: -x[1]):
        lines.append(f"   • {status}: <b>{count}</b>")

    if not report["status_counts"]:
        lines.append("   Bugun lid kelmagan.")

    return "\n".join(lines)
