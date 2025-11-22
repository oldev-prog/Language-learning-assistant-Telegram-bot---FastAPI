from sqlalchemy.orm import Mapped, DeclarativeBase, mapped_column, relationship
from sqlalchemy import Text, String, DateTime, ForeignKey
from time import time
from typing import Annotated
from datetime import datetime, timezone
from app.data.class_base import Base
from typing import List


intpk = Annotated[int, mapped_column(primary_key= True)]
strpk = Annotated[str, mapped_column(primary_key= True, default=None)]
time = Annotated[datetime, mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))]


class Word(Base):
    __tablename__ = 'words'

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int]
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    word: Mapped[str] = mapped_column(Text)
    translate: Mapped[str] = mapped_column(String(250))
    language: Mapped[str] = mapped_column(String(2))
    created_at: Mapped[time] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    review_time: Mapped[time] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now())
    interval: Mapped[int] = mapped_column(default=1)
    quality:  Mapped[int] = mapped_column(default=0)
    repetitions: Mapped[int] = mapped_column(default=0)

    user: Mapped['User'] = relationship(back_populates='words')


class WordRevers(Base):
    __tablename__ = 'revers_words'

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int]
    word: Mapped[str] = mapped_column(Text)
    translate: Mapped[str] = mapped_column(String(250))
    language: Mapped[str] = mapped_column(String(2))
    created_at: Mapped[time] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    review_time: Mapped[time] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now())
    interval: Mapped[int] = mapped_column(default=1)
    quality: Mapped[int] = mapped_column(default=0)
    repetitions: Mapped[int] = mapped_column(default=0)


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(unique=True)
    state: Mapped[str] = mapped_column(default='')
    native_lang: Mapped[str] = mapped_column(default='')
    lang_code: Mapped[str] = mapped_column(default='')
    last_word: Mapped[str] = mapped_column(default='')
    last_translate: Mapped[str] = mapped_column(default='')
    review_index: Mapped[int] = mapped_column(default=0)
    message_id: Mapped[int] = mapped_column(nullable=True)
    curr_command: Mapped[str] = mapped_column(nullable=True)
    invalid_reply_count: Mapped[int] = mapped_column(nullable=True)

    words: Mapped[List['Word']] = relationship(back_populates='user', lazy='selectin')

    def to_dict(self):
        return {
            'chat_id': self.chat_id,
            'state': self.state,
            'native_lang': self.native_lang,
            'lang_code': self.lang_code,
            'last_word': self.last_word,
            'last_translate': self.last_translate,
            'review_index': self.review_index,
        }