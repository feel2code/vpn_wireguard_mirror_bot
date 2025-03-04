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
    common_data, user_ids_tomorrow_ends = check_all_subscriptions()
    await bot.send_message(
        chat_id=ADMIN,
        text=f"Пользователям {common_data} необходимо отменить подписки и удалить их из базы.",
    )
    for user_id in user_ids_tomorrow_ends:
        await bot.send_message(
            chat_id=int(user_id),
            text="Напоминание о том, что ваша подписка завтра закончится. Вы можете продлить ее.",
        )


if __name__ == "__main__":
    asyncio.run(main())
