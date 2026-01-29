import logging
import os
import re

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

FACILITIES = {
    'BHM1': 'Early Accepts',
    'HSV1': 'Early Accepts',
    'PHX3': 'Early Accepts',
    'PHX5': 'Early Accepts',
    'PHX6': 'Early Accepts',
    'PHX7': 'Early Accepts',
    'PHX8': 'Early Accepts',
    'PHX9': 'Early Accepts',
    'LAX1': 'On-time Only',
    'LAX2': 'Early Accepts',
    'LAX4': 'On-time Only',
    'LAX5': 'On-time Only',
    'LAX9': 'On-time Only',
    'OAK3': 'Early Accepts',
    'OAK4': 'Early Accepts',
    'OAK5': 'Early Accepts',
    'OAK6': 'Early Accepts',
    'OAK7': 'Early Accepts',
    'ONT2': 'Early Accepts',
    'ONT3': 'Early Accepts',
    'ONT4': 'Early Accepts',
    'ONT5': 'Early Accepts',
    'ONT6': 'Early Accepts',
    'ONT8': 'Early Accepts',
    'ONT9': 'Early Accepts',
    'SMF3': 'On-time Only',
    'DEN4': 'Early Accepts',
    'BDL1': 'Early Accepts',
    'MCO5': 'Early Accepts',
    'MIA1': '50/50',
    'MIA5': 'Early Accepts',
    'TPA1': 'Early Accepts',
    'TPA2': 'Early Accepts',
    'ATL6': 'Early Accepts',
    'SAV3': 'Early Accepts',
    'SHV1': 'Early Accepts',
    'FWA4': 'On-time Only',
    'FWA6': 'Early Accepts',
    'IND1': 'Early Accepts',
    'IND2': 'Early Accepts',
    'IND3': 'Early Accepts',
    'IND4': 'Early Accepts',
    'IND5': 'Early Accepts',
    'IND9': 'Early Accepts',
    'MQJ1': 'On-time Only',
    'DDC1': 'Early Accepts',
    'MKC1': 'Early Accepts',
    'CVG1': 'Early Accepts',
    'CVG2': 'Early Accepts',
    'CVG3': 'Early Accepts',
    'CVG5': 'Early Accepts',
    'CVG7': 'Early Accepts',
    'CVG8': 'Early Accepts',
    'LEX1': 'Early Accepts',
    'LEX2': 'Early Accepts',
    'MKY1': 'On-time Only',
    'SDF1': 'Early Accepts',
    'SDF2': 'Early Accepts',
    'SDF4': 'Early Accepts',
    'SDF6': 'Early Accepts',
    'SDF7': 'Early Accepts',
    'SDF8': 'Early Accepts',
    'SDF9': 'Early Accepts',
    'BWI1': 'Early Accepts',
    'BWI2': 'Early Accepts',
    'BWI5': 'Early Accepts',
    'BOS1': 'Early Accepts',
    'BOS5': 'Early Accepts',
    'DET1': 'On-time Only',
    'MSP5': 'Early Accepts',
    'MCI5': 'Early Accepts',
    'LAS1': 'On-time Only',
    'LAS2': 'Early Accepts',
    'LAS7': 'On-time Only',
    'VGT2': 'Early Accepts',
    'EWR4': 'Early Accepts',
    'EWR5': 'Early Accepts',
    'EWR6': 'Early Accepts',
    'EWR7': 'Early Accepts',
    'EWR8': 'Early Accepts',
    'TEB9': 'Early Accepts',
    'JFK7': 'Early Accepts',
    'CLT5': 'Early Accepts',
    'CMH1': 'Early Accepts',
    'IOH1': 'On-time Only',
    'OKC1': 'Early Accepts',
    'PDX3': 'Early Accepts',
    'ABE2': 'Allentown, PA',  # if these are wrong, remove or fix
}

LOCATIONS = {
    'BHM1': 'Bessemer, AL',
    'HSV1': 'Madison, AL',
    'PHX3': 'Goodyear, AZ',
    'PHX5': 'Phoenix, AZ',
    'PHX6': 'Phoenix, AZ',
    'PHX7': 'Buckeye, AZ',
    'PHX8': 'Tolleson, AZ',
    'PHX9': 'Goodyear, AZ',
    'LAX1': 'San Bernardino, CA',
    'LAX2': 'Moreno Valley, CA',
    'LAX4': 'San Bernardino, CA',
    'LAX5': 'San Bernardino, CA',
    'LAX9': 'Fontana, CA',
    'OAK3': 'Tracy, CA',
    'OAK4': 'San Leandro, CA',
    'OAK5': 'Oakland, CA',
    'OAK6': 'Newark, CA',
    'OAK7': 'Fremont, CA',
    'ONT2': 'Ontario, CA',
    'ONT3': 'Ontario, CA',
    'ONT4': 'Fontana, CA',
    'ONT5': 'Moreno Valley, CA',
    'ONT6': 'San Bernardino, CA',
    'ONT8': 'Riverside, CA',
    'ONT9': 'Chino, CA',
    'SMF3': 'Stockton, CA',
    'DEN4': 'Aurora, CO',
    'BDL1': 'Windsor Locks, CT',
    'MCO5': 'Orlando, FL',
    'MIA1': 'Opa Locka, FL',
    'MIA5': 'Miami, FL',
    'TPA1': 'Tampa, FL',
    'TPA2': 'Ruskin, FL',
    'ATL6': 'Atlanta, GA',
    'SAV3': 'Savannah, GA',
    'SHV1': 'Romeoville, IL',
    'FWA4': 'Fort Wayne, IN',
    'FWA6': 'Fort Wayne, IN',
    'IND1': 'Indianapolis, IN',
    'IND2': 'Whitestown, IN',
    'IND3': 'Plainfield, IN',
    'IND4': 'Lebanon, IN',
    'IND5': 'Edinburgh, IN',
    'IND9': 'Whitestown, IN',
    'MQJ1': 'Greenfield, IN',
    # (keep adding if you want; missing ones are fine)
}

def extract_code(text: str):
    match = re.search(r"\b[A-Z]{3,4}\d+\b", (text or "").upper())
    return match.group(0) if match else None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Hi! Send me an Amazon facility code (e.g., FWA4) and I'll tell you the early arrival status.\n"
        "Statuses: Early Accepts ✅, On-time Only ❌, or 50/50 ⚖️"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    code = extract_code(update.message.text if update.message else "")

    if not code:
        await update.message.reply_text("Please send a valid Amazon facility code (e.g., FWA4).")
        return

    status = FACILITIES.get(code, "Unknown")
    location = LOCATIONS.get(code, "")
    loc_text = f"{location} - " if location else ""

    if status == "Unknown":
        await update.message.reply_text(f"{loc_text}{code}: Not found in my list.")
    else:
        emoji = "✅" if "Early" in status else "❌" if "Only" in status else "⚖️"
        await update.message.reply_text(f"{loc_text}{code}: {status} {emoji}")

def main() -> None:
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN is missing. Add it in Railway Variables.")

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot running (polling)...")
    app.run_polling()

if __name__ == "__main__":
    main()
