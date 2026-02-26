import os
import requests
from dotenv import load_dotenv
from app.web.webhook import WEBHOOK_URL

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')

set_webhook_url = f'https://api.telegram.org/bot{BOT_TOKEN}/setWebhook'
response = requests.post(set_webhook_url, data={'url': WEBHOOK_URL})

if response.json().get('ok'):
    print('Success!')
else:
    print('Error:', response.json())

check_url = f'https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo'
print(requests.get(check_url).json())

send_msg_url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'

bottom_url = f'https://api.telegram.org/bot{BOT_TOKEN}/editMessageReplyMarkup'

send_action_url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendChatAction'

send_document_url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendDocument'

answer_callback_url = f'https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery'

send_voice_url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendVoice'