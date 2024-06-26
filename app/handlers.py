# handlers.py
from aiogram import F, Router, Bot
from aiogram.enums import ChatType
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import logging

import app.keyboards as kb
import app.db as bd
import app.oxford_api as ox
from app.utils import HangmanGame

router = Router()


class GameStates(StatesGroup):
    playing = State()


@router.message(CommandStart())
async def cmd_start(message: Message):
    logging.info(f"User {message.from_user.id} called /start")
    await bd.add_chat_id_if_not_exists(message.chat.id)
    await message.reply(f"""
    Welcome to Hangman Bot! Here are the available commands:
    /start - Show this message
    /play - Start a new game
    /me - Show your score
    /top - Show top 10 players and scores
    /vocabulary - Show all saved words
    /word <word> - Get definitions and examples for a specific <word>
    """)


@router.message(Command('play'))
async def cmd_play(message: Message):
    logging.info(f"User {message.from_user.id} called /play")
    if message.chat.type == ChatType.PRIVATE:
        await message.reply("Choose difficulty", reply_markup=kb.difficulty)
    else:
        await message.reply("Please start the game in a private chat with the bot.")


@router.callback_query(F.data.in_(['easy', 'medium', 'hard']))
async def start_game(callback: CallbackQuery, state: FSMContext, bot: Bot):
    difficulty = callback.data
    logging.info(f"User {callback.from_user.id} started a game with difficulty {difficulty}")
    await callback.message.reply(f"Starting {difficulty} game...")
    await callback.message.delete()
    game = HangmanGame(callback.message.chat.first_name, callback.message.chat.id, difficulty=difficulty)
    await state.update_data(game=game)
    await state.set_state(GameStates.playing)
    await game.start_game(bot)


@router.message(Command('word'))
async def cmd_word(message: Message):
    try:
        data = message.text.split()[1].strip()
        logging.info(f"User {message.from_user.id} requested definition for word {data}")
        result = await ox.get_data(data, False)
    except IndexError:
        logging.warning(f"User {message.from_user.id} called /word without specifying a word")
        result = None
        await message.reply(
            'After the /word command, write the word whose definition you would like to know. i.e. /word <word>')
    if result:
        await message.answer('Definitions:')
        for i in range(len(result['definitions'])):
            await message.answer(f"{i + 1}) {result['definitions'][i]}")
        if result['examples']:
            await message.answer('Examples:')
            for i in range(len(result['examples'])):
                await message.answer(f"{i + 1}) {result['examples'][i]}")


@router.callback_query(F.data.in_(['get_hint', 'no_get_hint']))
async def cmd_hint(callback: CallbackQuery, state: FSMContext, bot: Bot):
    choice = callback.data
    logging.info(f"User {callback.from_user.id} chose {choice} for hint")
    if choice == 'get_hint':
        data = await state.get_data()
        game: HangmanGame = data.get('game')
        await callback.message.delete()
        if game:
            await game.give_hint(bot)
        else:
            await callback.message.reply("Start the game first.")
    else:
        await callback.message.delete()


@router.callback_query(F.data.in_(['get_definition', 'no_get_definition']))
async def cmd_definition(callback: CallbackQuery, state: FSMContext, bot: Bot):
    choice = callback.data
    logging.info(f"User {callback.from_user.id} chose {choice} for definition")
    if choice == 'get_definition':
        data = await state.get_data()
        game: HangmanGame = data.get('game')
        await callback.message.delete()
        if game:
            await game.give_definition(bot)
        else:
            await callback.message.reply("Start the game first")
    else:
        await callback.message.delete()


@router.callback_query(F.data.in_(['play_again', 'no_play_again']))
async def handle_play_again(callback: CallbackQuery, state: FSMContext, bot: Bot):
    choice = callback.data
    logging.info(f"User {callback.from_user.id} chose {choice} to play again")
    if choice == 'play_again':
        data = await state.get_data()
        game: HangmanGame = data.get('game')
        await callback.message.delete()
        if game:
            await game.reset_game_state()
            await game.start_game(bot)
    elif choice == 'no_play_again':
        await state.clear()
        await callback.message.edit_text("Maybe next time! Use /play to start a new game.")


@router.callback_query(F.data.in_(['word_to_database', 'no_word_to_database']))
async def adding_word_to_database(callback: CallbackQuery, state: FSMContext, bot: Bot):
    choice = callback.data
    logging.info(f"User {callback.from_user.id} chose {choice} to add word to database")
    data = await state.get_data()
    game: HangmanGame = data.get('game')
    if choice == 'word_to_database':
        await callback.message.delete()
        if game:
            await game.add_word(bot)
    else:
        await callback.message.delete()
        if game:
            await game.resetting_game(bot)


@router.message(Command('me'))
async def cmd_me(message: Message):
    logging.info(f"User {message.from_user.id} called /me")
    if message.chat.type == ChatType.PRIVATE:
        player_id = message.from_user.id
        player_name = message.chat.first_name
        score = await bd.get_score(player_id)
        if score is not None:
            await message.reply(f"Hello, {player_name}! Your current score is: {score}")
        else:
            await message.reply(f"Hello, {player_name}! You don't have a score yet.")
    else:
        await message.reply("You can only find out how many points you have by private messaging the bot :)")


@router.message(Command('top'))
async def cmd_top(message: Message):
    logging.info(f"User {message.from_user.id} called /top")
    limit = 10
    top_scores = await bd.get_top_scores(limit)

    if top_scores:
        response = "Top 10 Players:\n"
        for rank, (player_name, score) in enumerate(top_scores, start=1):
            response += f"{rank}. {player_name}: {score}\n"
    else:
        response = "No scores found."
    await message.reply(response)


@router.message(Command('vocabulary'))
async def cmd_vocabulary(message: Message):
    logging.info(f"User {message.from_user.id} called /vocabulary")
    if message.chat.type == ChatType.PRIVATE:
        result = await bd.get_player_words(message.chat.id)
        if result:
            await message.answer(result)
        else:
            await message.reply("Sorry, you don't have any words yet.")
    else:
        await message.reply("You can only view all your saved words via private bot messages :)")


@router.message(GameStates.playing)
async def guess_letter_or_word(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    logging.info(f"User {message.from_user.id} guessed: {message.text}")
    game: HangmanGame = data.get('game')
    if game:
        await game.handle_guess(bot, message.text.lower())
