# Should be addded to cron

import asyncio
from os import getenv

from aiogram import Bot
from dotenv import load_dotenv

from db_tools import check_all_subscriptions

load_dotenv(".env")
ADMIN = getenv("ADMIN")
TOKEN = getenv("BOT_TOKEN")


async def main() -> None:
    bot = Bot(token=TOKEN)
    await bot.send_message(
        chat_id=ADMIN,
        text=f"Пользователям с конфигами {data} необходимо отменить подписки. Удалите их из базы данных.",
    )


if __name__ == "__main__":
    data = check_all_subscriptions()
    asyncio.run(main())
