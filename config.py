import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv('eVars.env')

TOKEN = os.getenv('TOKEN')
DB_FILE = os.getenv('DB_FILE')
admin_id = int(os.getenv('ADMIN_ID'))

I18N_DOMAIN = os.getenv('BOT_NAME')
BASE_DIR = Path(__file__).parent
LOCALES_DIR = BASE_DIR / 'locales'

ITEMS_PER_PAGE = int(os.getenv('ITEMS_PER_PAGE'))

PAYMENT_TOKEN = os.getenv('PAYMENT_TOKEN')
