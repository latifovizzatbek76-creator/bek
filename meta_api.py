"""Meta Ads API — kunlik statistika."""
import requests
from datetime import datetime, timedelta
from config import META_ACCESS_TOKEN, META_AD_ACCOUNT_ID

GRAPH_URL = "https://graph.facebook.com/v18.0"


def get_adset_insights() -> list[dict]:
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    url = f"{GRAPH_URL}/act_{META_AD_ACCOUNT_ID}/insights"
    params = {
        "access_token": META_ACCESS_TOKEN,
        "time_range": f'{{"since":"{yesterday}","until":"{yesterday}"}}',
        "fields": "campaign_name,adset_name,spend,impressions,clicks,actions,cost_per_action_type",
        "level": "adset",
        "limit": 200,
    }
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json().get("data", [])


def build_meta_report() -> dict:
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%d.%m.%Y")
    insights  = get_adset_insights()

    report = {
        "date": yesterday,
        "total_spend": 0.0,
        "total_leads": 0,
        "avg_cpl": 0.0,
        "adsets": [],
    }

    lead_types = {"lead", "offsite_conversion.fb_pixel_lead", "onsite_conversion.lead_grouped"}

    for row in insights:
        spend  = float(row.get("spend", 0))
        leads  = sum(int(a["value"]) for a in row.get("actions", []) if a["action_type"] in lead_types)
        cpl    = next((float(c["value"]) for c in row.get("cost_per_action_type", []) if c["action_type"] in lead_types), 0.0)

        report["total_spend"] += spend
        report["total_leads"] += leads
        report["adsets"].append({
            "campaign": row.get("campaign_name", "—"),
            "adset":    row.get("adset_name", "—"),
            "spend":    round(spend, 2),
            "leads":    leads,
            "cpl":      round(cpl, 2),
        })

    if report["total_leads"] > 0:
        report["avg_cpl"] = round(report["total_spend"] / report["total_leads"], 2)

    return report


def format_meta_message(report: dict) -> str:
    lines = [
        f"📊 <b>META ADS HISOBOT</b> — {report['date']}",
        "━━━━━━━━━━━━━━━━━━━━",
        f"💰 Jami xarajat: <b>${report['total_spend']:,.2f}</b>",
        f"🎯 Jami lidlar: <b>{report['total_leads']}</b>",
        f"💵 O'rtacha CPL: <b>${report['avg_cpl']:,.2f}</b>",
        "",
        "📁 <b>Ad Set'lar:</b>",
    ]
    for i, ad in enumerate(report["adsets"], 1):
        lines.append(
            f"\n{i}. <b>{ad['adset']}</b>\n"
            f"   Kampaniya: {ad['campaign']}\n"
            f"   Xarajat: ${ad['spend']:,.2f} | Lidlar: {ad['leads']} | CPL: ${ad['cpl']:,.2f}"
        )
    if not report["adsets"]:
        lines.append("❌ Kecha ma'lumot topilmadi.")
    return "\n".join(lines)
