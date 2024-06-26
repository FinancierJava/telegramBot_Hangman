from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                           InlineKeyboardButton, InlineKeyboardMarkup)
from string import *

difficulty = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Easy', callback_data='easy'),
                                                    InlineKeyboardButton(text='Medium', callback_data='medium'),
                                                    InlineKeyboardButton(text='Hard', callback_data='hard')]])

resetting = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Yes', callback_data='play_again'),
                                                   InlineKeyboardButton(text='No', callback_data='no_play_again')]])

definitions = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Yes', callback_data='get_definition'),
                                                     InlineKeyboardButton(text='No',
                                                                          callback_data='no_get_definition')]])

hint = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Yes', callback_data='get_hint'),
                                              InlineKeyboardButton(text='No', callback_data='no_get_hint')]])

word_database = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text='Yes', callback_data='word_to_database'),
                      InlineKeyboardButton(text='No', callback_data='no_word_to_database')]])
