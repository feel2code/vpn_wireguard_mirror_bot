# Should be addded to cron

import asyncio
from os import getenv

from aiogram import Bot
from dotenv import load_dotenv

from db_tools import check_all_subscriptions, get_all_users

load_dotenv(".env")
ADMIN = getenv("ADMIN")
TOKEN = getenv("BOT_TOKEN")


async def main() -> None:
    """Check subscriptions and send messages to users."""
    bot = Bot(token=TOKEN)
    (
        common_data_vpn,
        common_data_proxy,
        user_ids_tomorrow_ends_vpn,
        user_ids_tomorrow_ends_proxy,
    ) = check_all_subscriptions()
    await bot.send_message(
        chat_id=ADMIN,
        text=(
            f"""Пользователям:\nVPN {common_data_vpn},\nPROXY {common_data_proxy}
                необходимо отменить подписки и удалить их из базы."""
        ),
    )
    for user_id in user_ids_tomorrow_ends_vpn:
        await bot.send_message(
            chat_id=int(user_id),
            text=(
                """Напоминание о том, что ваша подписка на VPN завтра закончится.
                   Вы можете продлить ее."""
            ),
        )
    for user_id in user_ids_tomorrow_ends_proxy:
        await bot.send_message(
            chat_id=int(user_id),
            text=(
                """Напоминание о том, что ваша подписка на PROXY завтра закончится.
                   Вы можете продлить ее."""
            ),
        )


async def send_message_to_all_users() -> None:
    """Send message to all users."""
    bot = Bot(token=TOKEN)
    all_users = get_all_users()
    for user_id in all_users:
        await bot.send_message(
            chat_id=int(user_id),
            text="Объявление: ",
        )


if __name__ == "__main__":
    asyncio.run(main())
