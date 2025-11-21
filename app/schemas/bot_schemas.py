from enum import Enum

class ReviewState(str, Enum):
    forgot = 'forgot'
    hard = 'hard'
    easy = 'easy'
    perfect = 'perfect'


class Commands(str, Enum):
    start = '/start'
    change_lang = '/change_lang'
    save = '/save'
    delete_word = '/delete_word'
    words_list = '/words_list'
    review = '/review'