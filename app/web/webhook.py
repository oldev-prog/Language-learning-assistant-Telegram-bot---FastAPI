import requests

BOT_TOKEN = '7768022070:AAH5K-SH3noqyCQ2rk-tdW3spnRqz0wYCgo'
WEBHOOK_URL = 'https://db52080d21c7.ngrok-free.app/telegram/webhook'

set_webhook_url = f'https://api.telegram.org/bot{BOT_TOKEN}/setWebhook'

response = requests.post(set_webhook_url, data={'url': WEBHOOK_URL})

print(response.json())
