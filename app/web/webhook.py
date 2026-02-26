import requests
from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
WEBHOOK_URL = 'https://edfdcaf7a8a2.ngrok-free.app/telegram/webhook'

set_webhook_url = f'https://api.telegram.org/bot{BOT_TOKEN}/setWebhook'

response = requests.post(set_webhook_url, data={'url': WEBHOOK_URL})


print(response.json())
