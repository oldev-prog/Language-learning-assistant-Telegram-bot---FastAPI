from pydantic import BaseModel, field_validator, ValidationError
from app.schemas.bot_schemas import Commands

class Chat(BaseModel):
    id: int

class Message(BaseModel):
    message_id: int
    chat: Chat
    text: str|None = None

    @field_validator('text')
    @classmethod
    def validate_text(cls, value: str) -> str:
        if value.startswith('/'):
            try:
                Commands(value)
            except ValueError:
                return 'invalid command'
        return value

class CallbackQuery(BaseModel):
    id: str
    data: str
    message: Message

class Update(BaseModel):
    update_id: int
    message: Message|None = None
    callback_query: CallbackQuery|None = None

