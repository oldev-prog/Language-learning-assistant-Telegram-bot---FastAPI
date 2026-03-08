from fastapi import FastAPI

app = FastAPI()

from app.web.webhook_router import webhook_router

app.include_router(webhook_router)
