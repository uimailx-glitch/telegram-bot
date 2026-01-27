import logging
import re
import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Dictionary of facilities: code -> status
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
    'ABE2': 'Early Accepts',
    'ABE3': 'Early Accepts',
    'AVP1': 'Early Accepts',
    'DPH1': 'Early Accepts',
    'MDT1': 'Early Accepts',
    'PHL1': 'Early Accepts',
    'PHL4': 'Early Accepts',
    'PHL5': 'Early Accepts',
    'PHL6': 'Early Accepts',
    'PHL7': 'Early Accepts',
    'PHL9': 'Early Accepts',
    'PIT5': 'Early Accepts',
    'CAE1': 'Early Accepts',
    'GSP1': 'Early Accepts',
    'BNA1': 'Early Accepts',
    'BNA2': 'Early Accepts',
    'BNA3': 'Early Accepts',
    'BNA5': 'Early Accepts',
    'BNA6': 'On-time Only',
    'CHA1': 'Early Accepts',
    'CHA2': 'Early Accepts',
    'MEM1': 'Early Accepts',
    'MEM4': 'On-time Only',
    'TYS1': 'Early Accepts',
    'DFW6': 'Early Accepts',
    'DFW7': 'Early Accepts',
    'DFW8': 'Early Accepts',
    'DFW9': 'Early Accepts',
    'HOU1': 'Early Accepts',
    'IAH3': 'On-time Only',
    'SAT1': 'Early Accepts',
    'XHH3': 'Early Accepts',
    'ORF2': '50/50',
    'ORF3': 'Early Accepts',
    'RIC1': 'Early Accepts',
    'RIC2': 'Early Accepts',
    'RIC5': 'Early Accepts',
    'BFI1': 'Early Accepts',
    'BFI3': 'Early Accepts',
    'BFI5': 'Early Accepts',
    'BFIX': 'Early Accepts',
    'SEA6': 'Early Accepts',
    'SEA8': 'Early Accepts',
    'MKE1': 'Early Accepts',
    'MKE5': 'Early Accepts',
    'MKE7': 'Early Accepts'
}

# Locations
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
    'DDC1': 'Des Moines, IA',
    'MKC1': 'Kansas City, KS',
    'CVG1': 'Hebron, KY',
    'CVG2': 'Hebron, KY',
    'CVG3': 'Hebron, KY',
    'CVG5': 'Hebron, KY',
    'CVG7': 'Hebron, KY',
    'CVG8': 'Hebron, KY',
    'LEX1': 'Lexington, KY',
    'LEX2': 'Lexington, KY',
    'MKY1': 'Louisville, KY',
    'SDF1': 'Louisville, KY',
    'SDF2': 'Louisville, KY',
    'SDF4': 'Louisville, KY',
    'SDF6': 'Louisville, KY',
    'SDF7': 'Louisville, KY',
    'SDF8': 'Louisville, KY',
    'SDF9': 'Louisville, KY',
    'BWI1': 'Baltimore, MD',
    'BWI2': 'Baltimore, MD',
    'BWI5': 'Baltimore, MD',
    'BOS1': 'Boston, MA',
    'BOS5': 'North Reading, MA',
    'DET1': 'Livonia, MI',
    'MSP5': 'Lakeville, MN',
    'MCI5': 'Kansas City, MO',
    'LAS1': 'Henderson, NV',
    'LAS2': 'North Las Vegas, NV',
    'LAS7': 'Las Vegas, NV',
    'VGT2': 'Las Vegas, NV',
    'EWR4': 'Elizabeth, NJ',
    'EWR5': 'Avenel, NJ',
    'EWR6': 'Robbinsville, NJ',
    'EWR7': 'Cranbury, NJ',
    'EWR8': 'Edison, NJ',
    'TEB9': 'Teterboro, NJ',
    'JFK7': 'Staten Island, NY',
    'CLT5': 'Charlotte, NC',
    'CMH1': 'Etna, OH',
    'IOH1': 'Columbus, OH',
    'OKC1': 'Oklahoma City, OK',
    'PDX3': 'Portland, OR',
    'ABE2': 'Allentown, PA',
    'ABE3': 'Allentown, PA',
    'AVP1': 'Hazleton, PA',
    'DPH1': 'Du Bois, PA',
    'MDT1': 'Middletown, PA',
    'PHL1': 'Philadelphia, PA',
    'PHL4': 'Philadelphia, PA',
    'PHL5': 'Upper Darby, PA',
    'PHL6': 'Allentown, PA',
    'PHL7': 'Philadelphia, PA',
    'PHL9': 'Bristol, PA',
    'PIT5': 'Pittsburgh, PA',
    'CAE1': 'West Columbia, SC',
    'GSP1': 'Greer, SC',
    'BNA1': 'Nashville, TN',
    'BNA2': 'Lebanon, TN',
    'BNA3': 'Mount Juliet, TN',
    'BNA5': 'Gallatin, TN',
    'BNA6': 'Clarksville, TN',
    'CHA1': 'Chattanooga, TN',
    'CHA2': 'Chattanooga, TN',
    'MEM1': 'Memphis, TN',
    'MEM4': 'Memphis, TN',
    'TYS1': 'Alcoa, TN',
    'DFW6': 'Dallas, TX',
    'DFW7': 'Fort Worth, TX',
    'DFW8': 'Haslet, TX',
    'DFW9': 'Schertz, TX',
    'HOU1': 'Houston, TX',
    'IAH3': 'Houston, TX',
    'SAT1': 'San Antonio, TX',
    'XHH3': 'Salt Lake City, UT',
    'ORF2': 'Chesapeake, VA',
    'ORF3': 'Virginia Beach, VA',
    'RIC1': 'Richmond, VA',
    'RIC2': 'Richmond, VA',
    'RIC5': 'Richmond, VA',
    'BFI1': 'Seattle, WA',
    'BFI3': 'Seattle, WA',
    'BFI5': 'Seattle, WA',
    'BFIX': 'Seattle, WA',
    'SEA6': 'Seattle, WA',
    'SEA8': 'Seattle, WA',
    'MKE1': 'Milwaukee, WI',
    'MKE5': 'Oak Creek, WI',
    'MKE7': 'Pleasant Prairie, WI'
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("Spy: /start command received from user!")
    await update.message.reply_text(
        'Hi! Send me an Amazon facility code (e.g., FWA4) and I\'ll tell you if it accepts early arrivals or not.\n'
        'Statuses: Early Accepts, On-time Only, or 50/50.',
        parse_mode=ParseMode.MARKDOWN
    )

def extract_code(text: str) -> str:
    match = re.search(r'\b[A-Z]{3,4}\d+\b', text.upper())
    return match.group(0) if match else None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("Spy: Message received from user!")
    text = update.message.text
    code = extract_code(text)
    logger.info(f"Spy: Extracted code '{code}' from message")
  
    if not code:
        await update.message.reply_text('Please send a valid Amazon facility code (e.g., FWA4).')
        return
  
    status = FACILITIES.get(code, 'Unknown')
    location = LOCATIONS.get(code, '')
    loc_text = f'{location} - ' if location else ''
    if status == 'Unknown':
        await update.message.reply_text(f'{loc_text}{code}: Facility {code} not found in my list. It might accept early—check latest info!')
    else:
        emoji = '✅' if 'Early' in status else '❌' if 'Only' in status else '⚖️'
        await update.message.reply_text(f'{loc_text}{code}: {status} {emoji}')
   
    logger.info(f"Processed code '{code}' for user {update.effective_user.id}: {status}")

def create_app() -> Flask:
    TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '8559305303:AAEiZ1AehghmCDlLxamTr_iFvJC3aAMquzk')  # Your token added here (fallback)
    logger.info(f"Bot token loaded (length: {len(TOKEN)}) from {'env var' if os.environ.get('TELEGRAM_BOT_TOKEN') else 'fallback'}")
    app = Flask(__name__)

    application = Application.builder().token(TOKEN).build()
   
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    @app.route(f'/{TOKEN}', methods=['POST'])
    def webhook():
        try:
            update = Update.de_json(request.get_json(force=True), application.bot)
            application.process_update(update)
            logger.info("Webhook update processed")
            return 'OK'
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return 'Error', 500

    @app.route('/set_webhook', methods=['GET'])
    def set_webhook():
        webhook_url = f"https://{request.host}/{TOKEN}"
        try:
            application.bot.set_webhook(url=webhook_url)
            logger.info(f"Webhook set: {webhook_url}")
            return f"Webhook set to {webhook_url}"
        except Exception as e:
            logger.error(f"Set webhook error: {e}")
            return f"Error setting webhook: {e}"

    @app.route('/')
    def home():
        return "Amazon Facility Bot is running! Visit /set_webhook to activate."

    logger.info("Flask app created successfully")
    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
