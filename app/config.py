import os
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('http_proxy', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('https_proxy', None)
import requests

BOT_TOKEN = '7768022070:AAH5K-SH3noqyCQ2rk-tdW3spnRqz0wYCgo'
WEBHOOK_URL = ('https://543c52558d9f.ngrok-free.app/webhook')

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