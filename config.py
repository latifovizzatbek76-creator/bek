import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_GROUP_ID  = int(os.getenv("TELEGRAM_GROUP_ID", "0"))

META_ACCESS_TOKEN  = os.getenv("META_ACCESS_TOKEN")
META_AD_ACCOUNT_ID = os.getenv("META_AD_ACCOUNT_ID")

REPORT_HOUR   = int(os.getenv("REPORT_HOUR",   "9"))
REPORT_MINUTE = int(os.getenv("REPORT_MINUTE", "0"))
TIMEZONE      = os.getenv("TIMEZONE", "Asia/Tashkent")

PORT = int(os.getenv("PORT", "8000"))
