# Should be addded to cron

import asyncio
import subprocess
from os import getenv

from aiogram import Bot
from dotenv import load_dotenv

from db_tools import check_all_subscriptions, delete_user_subscription, get_all_users

load_dotenv(".env")
ADMIN = getenv("ADMIN")
TOKEN = getenv("BOT_TOKEN")


def delete_obfuscated_user_vpn_conf(obfuscated_user: str) -> bool:
    """Delete obfuscated user configuration file via automated sh script."""
    try:
        result = subprocess.run(
            ["sh", "delete_config.sh", obfuscated_user], capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"Error deleting vpn conf: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"Error deleting vpn conf: {e}")
        return False


def delete_obfuscated_user_proxy_conf(obfuscated_user: str) -> bool:
    """Delete obfuscated user configuration file via automated sh script."""
    try:
        result = subprocess.run(
            ["sh", "delete_proxy.sh", obfuscated_user], capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"Error deleting proxy conf: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"Error deleting proxy conf: {e}")
        return False


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
                будут отменены подписки и удалены из базы."""
        ),
    )
    for obfuscated_user in common_data_vpn:
        if delete_obfuscated_user_vpn_conf(obfuscated_user):
            print(f"Deleted VPN config for user: {obfuscated_user}")
            delete_user_subscription(obfuscated_user, 0)
    for obfuscated_user in common_data_proxy:
        if delete_obfuscated_user_proxy_conf(obfuscated_user):
            print(f"Deleted PROXY config for user: {obfuscated_user}")
            delete_user_subscription(obfuscated_user, 1)

    user_ids_tomorrow_ends_vpn = (
        [user_ids_tomorrow_ends_vpn]
        if isinstance(user_ids_tomorrow_ends_vpn, int)
        else user_ids_tomorrow_ends_vpn
    )
    user_ids_tomorrow_ends_proxy = (
        [user_ids_tomorrow_ends_proxy]
        if isinstance(user_ids_tomorrow_ends_proxy, int)
        else user_ids_tomorrow_ends_proxy
    )
    for user_id in user_ids_tomorrow_ends_vpn:
        await bot.send_message(
            chat_id=int(user_id),
            text=(
                """Напоминание о том, что ваша подписка на неVPN завтра закончится.
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
