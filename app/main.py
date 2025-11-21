from fastapi import FastAPI
import httpx
from app.data.user_crud import UserCRUD
from app.bot.telegram_bot import TelegramBot, Services
from app.dependencies import db
from app.web.command_dispatcher import CommandDispatcher
from app.web.state_dispatcher import StateDispatcher
from app.telegram_utils.start_funcs import StartFuncs

app = FastAPI()

client = httpx.AsyncClient()
user_crud = UserCRUD(db)
services = Services(db, client)
bot = TelegramBot(services)
command_dispatcher = CommandDispatcher(bot, services, user_crud, client)
state_dispatcher = StateDispatcher(bot, db)
start_funcs = StartFuncs()

from app.web.webhook_router import webhook_router

app.include_router(webhook_router)