import asyncio
import datetime
import logging
import sqlite3
from aiogram import Bot
from config import TOKEN


def get_summer_progress():
    current_date = datetime.date.today()
    summer_start = datetime.date(current_date.year, 6, 1)
    summer_end = datetime.date(current_date.year, 8, 31)

    if current_date < summer_start:
        return "Summer hasn't started yet!"
    elif current_date > summer_end:
        return "Summer has ended!"

    total_days_of_summer = (summer_end - summer_start).days
    days_passed = (current_date - summer_start).days

    progress_percentage = (days_passed / total_days_of_summer) * 100
    return f"{progress_percentage:.2f}% of the summer has already passed. Spend your time wisely :)"


def fetch_user_ids():
    logging.info("Fetching user ids...")
    conn = sqlite3.connect('hangman.db')
    cursor = conn.cursor()
    cursor.execute('SELECT player_id FROM scores')
    user_ids = cursor.fetchall()
    conn.close()
    return [user_id[0] for user_id in user_ids]


async def send_summer_progress():
    bot = Bot(token=TOKEN)
    user_ids = fetch_user_ids()
    message = get_summer_progress()

    for user_id in user_ids:
        try:
            await bot.send_message(user_id, message)
        except Exception as e:
            logging.error(f"Failed to send message to {user_id}: {e}")

    await bot.session.close()


if __name__ == '__main__':
    asyncio.run(send_summer_progress())
