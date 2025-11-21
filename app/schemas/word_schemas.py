from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime

class Language(str, Enum):
    en = "en"
    fr = "fr"
    ja = "ja"
    ko = "ko"
    ru = "ru"
    es = "es"
    it = "it"
    de = "de"
    pt = "pt"
    zh = "zh"
    ar = "ar"
    hi = "hi"
    bn = "bn"
    tr = "tr"
    vi = "vi"
    th = "th"
    pl = "pl"
    uk = "uk"
    ms = "ms"
    sw = "sw"
    el = "el"
    ro = "ro"
    la = "la"
    no = "no"


class WordPOST(BaseModel):
    word: str = Field(..., min_length=1, max_length=100)
    translate: str = Field(..., min_length=1, max_length=100)
    language: Language
    review_time: datetime
    quality: int = Field(..., ge=0, le=5)
    repetitions: int = Field(..., ge=0)


class WordGET(WordPOST):
    id: int