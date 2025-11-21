from urllib import request

from fastapi import APIRouter, Depends, HTTPException, status, Request, Body

from app.bot.telegram_bot import TelegramBot
from app.data.models import User
# from app.main import bot
from app.decorators import except_timeout
from fastapi.responses import JSONResponse


words_router = APIRouter(prefix="/words", tags=["words"])

@words_router.get('/{chat_id}/words_list',response_model=None, status_code=status.HTTP_200_OK)
@except_timeout
async def handle_words_get(chat_id: int, bot: TelegramBot):
    return await bot.send_words_list(chat_id)


@words_router.post('/save', status_code=status.HTTP_201_CREATED)
@except_timeout
async def handle_save_word(request: Request, user_crud, bot: TelegramBot):

    data = await request.json()
    word = data.get("word")
    chat_id = data.get("chat_id")
    user_state = await user_crud.get_user(chat_id)

    await bot.save_word(word, chat_id, user_state)
    return JSONResponse(
        {
            'success': True, 'details':'word has been successfully saved'
        }
    )

@words_router.delete('/{chat_id}/delete', status_code=status.HTTP_204_NO_CONTENT)
@except_timeout
async def handler_delete_word(word: str, chat_id: int, user_state: User):
    await bot.delete_word(word, chat_id, user_state)
    return JSONResponse(
        {
            'success': True, 'details': 'word has been successfully deleted'
        }
    )


review_router = APIRouter(prefix="/review", tags=["review"])

@review_router.put('/review', status_code=status.HTTP_200_OK)
@except_timeout
async def handle_review(request: Request):
    chat_id = request.get('chat_id')
    msg = await request.get('message')
    user_state = await user_crud.get_user(chat_id)
    await bot.spaced_review(chat_id, msg, user_state)
    return JSONResponse(
        {
            'success': True, 'details': 'review has been successfully finished'
        }
    )


youtube_video_router = APIRouter(prefix="/youtube", tags=["youtube"])

@youtube_video_router.post('/', status_code=status.HTTP_201_CREATED)
@except_timeout
async def handle_youtube_video(request: Request):
    chat_id = request.get('chat_id')
    user_state = await user_crud.get_user(chat_id)

    await bot.send_youtube_video(chat_id, user_state)
    return JSONResponse(
        {
            'success': True, 'details': 'youtube video has been successfully sent'
        }
    )


pronunciation_router = APIRouter(prefix="/pronunciation", tags=["pronunciation"])

@pronunciation_router.post('/pronunciation', status_code=status.HTTP_201_CREATED)
@except_timeout
async def handle_pronunciation(request: Request):
    chat_id = request.get('chat_id')
    user_state = await user_crud.get_user(chat_id)
    word = user_state.last_word
    await bot.send_pronunciation(chat_id, word)
    return JSONResponse(
        {
            'success': True, 'details': 'pronunciation has been successfully sent'
        }
    )


explanation_router = APIRouter(prefix="/explanation", tags=["explanation"])

@explanation_router.post('/explanation', status_code=status.HTTP_201_CREATED)
@except_timeout
async def handle_explanation(request: Request):
    chat_id = request.get('chat_id')
    user_state = await user_crud.get_user(chat_id)
    word = user_state.last_word
    await bot.explain_word(chat_id, word, user_state)
    return JSONResponse(
        {
            'success': True, 'details': 'explanation has been successfully sent'
        }
    )