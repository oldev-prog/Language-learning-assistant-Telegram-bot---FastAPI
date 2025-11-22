from enum import Enum

class ReviewState(str, Enum):
    forgot = 'forgot'
    hard = 'hard'
    easy = 'easy'
    perfect = 'perfect'


class Commands(str, Enum):
    start = '/start'
    change_native_lang = '/change_native_lang'
    change_learning_lang = '/change_learning_lang'
    save = '/save_word'
    delete_word = '/delete_word'
    words_list = '/words_list'
    review = '/repeating'
    reverse_review = '/reverse_repeating'