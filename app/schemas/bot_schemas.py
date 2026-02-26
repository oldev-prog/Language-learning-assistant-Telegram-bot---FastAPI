from enum import Enum

class ReviewState(str, Enum):
    '''A scheme for validating user responses during word repetition.'''

    forgot = 'forgot'
    hard = 'hard'
    easy = 'easy'
    perfect = 'perfect'


class Commands(str, Enum):
    '''Scheme for validating commands received from the user.'''

    start = '/start'
    change_native_lang = '/change_native_lang'
    change_learning_lang = '/change_learning_lang'
    save = '/save_word'
    delete_word = '/delete_word'
    words_list = '/words_list'
    review = '/repeating'
    reverse_review = '/reverse_repeating'