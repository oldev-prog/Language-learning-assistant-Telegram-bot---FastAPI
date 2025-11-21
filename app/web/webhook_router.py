from app.schemas.request_schemas import Update
from app.web.services_routers import *
from app.dependencies import *
from app.dependencies import session_dep
from app.data.user_crud import UserCRUD
from app.main import *
from app.telegram_utils.utils import answer_callback
from app.telegram_utils.utils import update_state_to_await
import asyncio

webhook_router = APIRouter(prefix='/telegram', tags=["Webhook"])

@webhook_router.post('/webhook', status_code=status.HTTP_200_OK)
async def telegram_webhook(
        request: Update,
):
    message = request.message
    callback = request.callback_query
    print(f'callback: {callback}')
    msg_data = message or (callback.message if callback else None)

    if not msg_data:
        return {'success': False, 'details': 'no data'}

    chat_id = msg_data.chat.id

    msg_id = msg_data.message_id

    user_states = await user_crud.check_exists(chat_id)

    if message:
        text = message.text

        if text in command_dispatcher.commands:
            return await command_dispatcher.dispatch(text, user_states, chat_id, client, db, msg_id)
        return await state_dispatcher.dispatch(text, user_states, chat_id, client, msg_id)

    if callback:
        data_value = callback.data

        await answer_callback(callback.id, client)

        if data_value == 'pronounce':

            await update_state_to_await(user_states, db)

            asyncio.create_task(bot.send_pronunciation(chat_id=chat_id, user_state=user_states, reply_to_id=msg_id))
            return JSONResponse(
                {
                    'success': True, 'details': 'pronunciation has been successfully sent'
                }
            )
        elif data_value == 'youtube':

            await update_state_to_await(user_states, db)

            asyncio.create_task(bot.send_youtube_video(chat_id=chat_id, user_state=user_states))
            return JSONResponse(
                {
                    'success': True, 'details': 'youtube video has been successfully sent'
                }
            )

    return {'success': True}
