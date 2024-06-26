import asyncio
from aiogram import Bot, Dispatcher
from app.handlers import router
import logging
from config import TOKEN

logging.basicConfig(level=logging.INFO, filename='logs.txt', filemode='a',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info('Ctrl+C pressed. Stopping.')
