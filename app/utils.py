import random
from aiogram import Bot
import app.keyboards as kb
import app.oxford_api as ox


class HangmanGame:
    def __init__(self, user_name: str, chat_id: int, difficulty: str):
        self.name = user_name
        self.chat_id = chat_id
        self.difficulty = difficulty
        self.word = random.choice(self.load_words(difficulty))
        self.guessed_letters = set()
        self.wrong_guessed_letters = set()
        self.wrong_guesses = 0
        self.max_wrong_guesses = {'easy': 8, 'medium': 7, 'hard': 6}[difficulty]
        self.hints_used = 0
        self.used_definition = False
        self.end_game = False
        self.made_mistake = False
        self.get_score = False
        self.saved_word = False

    async def start_game(self, bot: Bot):
        await bot.send_message(self.chat_id, self.get_display_word())
        await bot.send_message(self.chat_id, "Guess a letter:")

    def get_display_word(self) -> str:
        return ' '.join([letter if letter in self.guessed_letters else '_' for letter in self.word])

    async def handle_guess(self, bot: Bot, data: str):
        self.made_mistake = False
        if self.end_game:
            return
        if self.is_word_guessed():
            await self.handle_game_end(bot)
            return

        if len(data) == 1:
            await self.handle_letter_guess(bot, data)
        else:
            await self.handle_word_guess(bot, data)

    async def handle_letter_guess(self, bot: Bot, letter: str):
        if letter in self.guessed_letters:
            await bot.send_message(self.chat_id, f"You already guessed the letter '{letter}'. Try again.")
        elif letter in self.word:
            self.guessed_letters.add(letter)
            if self.is_word_guessed():
                await self.handle_game_end(bot)
            else:
                await self.send_game_status(bot)
        elif letter in self.wrong_guessed_letters:
            await bot.send_message(self.chat_id, f"You already tried the letter '{letter}'. Try something else.")
        else:
            await self.record_wrong_guess(letter, bot)

    async def handle_word_guess(self, bot: Bot, whole_word: str):
        if whole_word == self.word:
            self.guessed_letters.update(self.word)
            await self.handle_game_end(bot)
        else:
            await self.record_wrong_guess(None, bot)

    async def send_game_status(self, bot: Bot):
        await bot.send_message(self.chat_id, self.get_display_word())
        if self.made_mistake:
            if not self.used_definition:
                await self.suggesting_definition(bot)
            elif self.hints_used < 2:
                await self.suggesting_hint(bot)

    async def send_wrong_guess_message(self, bot: Bot):
        remaining_guesses = self.max_wrong_guesses - self.wrong_guesses
        await bot.send_message(self.chat_id, f"Wrong guess! You have {remaining_guesses} guesses left.")
        await self.send_game_status(bot)

    async def record_wrong_guess(self, letter: str, bot: Bot):
        self.wrong_guesses += 1
        self.made_mistake = True
        if letter:
            self.wrong_guessed_letters.add(letter)
        if self.wrong_guesses >= self.max_wrong_guesses:
            await self.handle_game_end(bot)
        else:
            await self.send_wrong_guess_message(bot)

    async def suggesting_definition(self, bot: Bot):
        await bot.send_message(self.chat_id, 'Would you like definitions and examples of how the word is used?',
                               reply_markup=kb.definitions)

    async def suggesting_hint(self, bot: Bot):
        await bot.send_message(self.chat_id, 'Would you like a random letter in your word to be revealed?',
                               reply_markup=kb.hint)

    async def handle_game_end(self, bot: Bot):
        self.end_game = True
        if not self.get_score:
            from app.db import save_score
            points = self.calculate_points()
            await save_score(self.chat_id, self.name, points)
            self.get_score = True

        message = f"Congratulations! You've guessed the word: {self.word}\nWould you like to save this word in your database?" if self.is_word_guessed() else f"Game over! The word was: {self.word}\nWould you like to save this word in your database?"
        await bot.send_message(self.chat_id, message, reply_markup=kb.word_database)

    async def reset_game_state(self):
        self.__init__(self.name, self.chat_id, self.difficulty)

    async def give_definition(self, bot: Bot):
        result = await ox.get_data(self.word, True)
        if result:
            self.used_definition = True
            await bot.send_message(self.chat_id, 'Definitions:\n' + '\n'.join(
                f"{i + 1}) {definition}" for i, definition in enumerate(result['definitions'])))
            if result['examples']:
                await bot.send_message(self.chat_id, 'Examples:\n' + '\n'.join(
                    f"{i + 1}) {example}" for i, example in enumerate(result['examples'])))

    async def give_hint(self, bot: Bot):
        available_letters = [letter for letter in self.word if letter not in self.guessed_letters]
        if available_letters:
            hint_letter = random.choice(available_letters)
            self.guessed_letters.add(hint_letter)
            self.hints_used += 1
            self.made_mistake = False
            await bot.send_message(self.chat_id, f"Hint: The word contains the letter '{hint_letter}'.")
            if self.is_word_guessed():
                await self.send_game_status(bot)
                await self.handle_game_end(bot)
            else:
                await self.send_game_status(bot)
        else:
            await bot.send_message(self.chat_id, "No hint available.")

    async def add_word(self, bot: Bot):
        self.saved_word = True
        from app.db import save_word
        res = await save_word(self.chat_id, self.word)
        message = f"The word '{self.word}' was successfully saved" if res else f"The word '{self.word}' is already in the database"
        await bot.send_message(self.chat_id, message)
        await self.resetting_game(bot)

    async def resetting_game(self, bot: Bot):
        await bot.send_message(self.chat_id, 'Would you like to play again?', reply_markup=kb.resetting)

    def calculate_points(self) -> int:
        if len(self.guessed_letters) == len(set(self.word)):
            difficulty_multiplier = {'hard': 2, 'medium': 1.6, 'easy': 1.2}[self.difficulty]
            hints_multiplier = {0: 1.5, 1: 1.2, 2: 1}[self.hints_used]
            word_length_multiplier = 1.2 if len(set(self.word)) >= 3 else 1
            points = round(10 * difficulty_multiplier * hints_multiplier * word_length_multiplier)
        else:
            difficulty_multiplier = {'hard': 1.2, 'medium': 1.5, 'easy': 2}[self.difficulty]
            hints_multiplier = {0: 1, 1: 1.5, 2: 2}[self.hints_used]
            word_length_multiplier = 1.2 if len(set(self.word)) <= 3 else 1
            points = round(-10 * difficulty_multiplier * hints_multiplier * word_length_multiplier)
        return points

    def load_words(self, difficulty: str) -> list:
        path = f'words_fold/{difficulty}.txt'
        with open(path, 'r') as file:
            return [line.split()[0].strip() for line in file if len(line.split()[0].strip()) >= 3]

    def is_word_guessed(self) -> bool:
        return all(letter in self.guessed_letters for letter in self.word)
