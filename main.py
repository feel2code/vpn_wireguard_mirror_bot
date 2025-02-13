import asyncio
import logging
import shlex
import subprocess
import sys
from os import getenv
from uuid import uuid4

from aiogram import Bot, Dispatcher, F, Router, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import (CallbackQuery, FSInputFile, InlineKeyboardMarkup,
                           LabeledPrice, Message, PreCheckoutQuery)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

from db_tools import (check_subscription_end, delete_user,
                      get_obfuscated_user_conf, need_to_update_user)

logger = logging.getLogger(__name__)
invoices_router = Router(name=__name__)


load_dotenv(".env")
DEMO_REGIME = bool(int(getenv("DEMO_REGIME")))
SERVICE_NAME = getenv("SERVICE_NAME")
ADMIN = getenv("ADMIN")
TOKEN = getenv("BOT_TOKEN")
FS_USER = getenv("FS_USER")
dp = Dispatcher()

if DEMO_REGIME:
    ccy = {
        "currency": "demo",
        "currency_value": 1,
    }
else:
    ccy = {
        "currency": "real",
        "currency_value": 91,
    }


def subscribe_management_kb() -> InlineKeyboardMarkup:
    """
    subscribe management keyboard
    """
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Купить подписку", callback_data="subscribe")
    kb.button(text="🗑️ Отменить подписку", callback_data="unsubscribe")
    kb.button(text="ℹ️  Инструкция", callback_data="instruction")
    kb.button(
        text="👽 Проверить подписку", callback_data="check_end_date_of_subscription"
    )
    kb.adjust(2, 2, 1)
    return kb.as_markup()


def home_kb() -> InlineKeyboardMarkup:
    """
    home keyboard
    """
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Купить подписку", callback_data="subscribe")
    kb.button(text="😢 Назад", callback_data="home")
    kb.adjust(2, 2, 1)
    return kb.as_markup()


def accept_kb() -> InlineKeyboardMarkup:
    """
    accept terms of service
    """
    kb = InlineKeyboardBuilder()
    kb.button(text="ПРИНИМАЮ", callback_data="accept")
    kb.adjust(2, 2, 1)
    return kb.as_markup()


@invoices_router.callback_query(F.data.startswith("check_end_date_of_subscription"))
async def check_end_date_of_subscription(call: CallbackQuery) -> None:
    """
    check end date of the subscription
    """
    conf_to_check = get_obfuscated_user_conf(call.from_user.id)
    if conf_to_check:
        await call.message.answer(
            f"Ваша подписка действует до: {check_subscription_end(call.from_user.id)}"
        )
        return
    await call.message.answer(
        f"Действующая подписка на {SERVICE_NAME} не найдена!",
    )


@invoices_router.callback_query(F.data.startswith("subscribe"))
async def subscribe(call: CallbackQuery) -> None:
    """
    subscribe to the service
    """
    await call.message.answer_invoice(
        title="Приобрести подписку",
        description=f"Подписка на 30 дней на {SERVICE_NAME}",
        prices=[
            LabeledPrice(label=ccy["currency"].title(), amount=ccy["currency_value"]),
        ],
        payload=ccy["currency"],
        currency="XTR",
    )


@invoices_router.message(F.successful_payment)
async def successful_payment(message: Message, bot: Bot) -> None:
    """
    Successful payment handler and create config file
    then send it to the user
    """
    user_id = message.from_user.id
    uuid_gen = uuid4()

    if DEMO_REGIME:
        await bot.refund_star_payment(
            user_id=message.from_user.id,
            telegram_payment_charge_id=message.successful_payment.telegram_payment_charge_id,
        )
        await message.answer("Demo. Your payment has been refunded.")
        need_to_update_user(user_id, f"{user_id}_{uuid_gen}")
        return

    await message.answer(
        f"""Спасибо за покупку подписки на {SERVICE_NAME}!
        Ваш ID платежа: {message.successful_payment.telegram_payment_charge_id}""",
        message_effect_id="5104841245755180586",  # stars effect
    )
    if not need_to_update_user(user_id, f"{user_id}_{uuid_gen}"):
        subprocess.run(
            shlex.split(f"/{FS_USER}/vpn_wireguard_mirror_bot/./create_config.sh {user_id}_{uuid_gen}")
        )
        await bot.send_document(
            chat_id=user_id,
            document=FSInputFile(f"/{FS_USER}/{user_id}_{uuid_gen}.conf"),
        )
        return

    await message.answer("Подписка продлена на месяц.")


@invoices_router.callback_query(F.data.startswith("unsubscribe"))
async def unsubscribe(call: CallbackQuery, bot: Bot) -> None:
    """
    unsubscribe from the service
    """
    conf_to_be_revoked = get_obfuscated_user_conf(call.from_user.id)
    if conf_to_be_revoked:
        await call.message.answer(
            f"Заявка на отмену подписки на {SERVICE_NAME} отправлена в службу поддержки.",
        )
        await bot.send_message(
            chat_id=ADMIN,
            text=f"Пользователю с конфигом {conf_to_be_revoked} необходимо отменить подписку. Удален из базы.",
        )
        delete_user(call.from_user.id)
        return

    await call.message.answer(
        f"Действующая подписка на {SERVICE_NAME} не найдена!",
    )


@invoices_router.callback_query(F.data.startswith("instruction"))
async def get_instruction(call: CallbackQuery) -> None:
    """
    instruction for the service install
    """
    await call.message.answer(
        f"""
        Инструкция по установке:
        1. Установите приложение Wireguard на свой телефон

        * Для iOS: https://apps.apple.com/us/app/wireguard/id1441195209
        * Для Android: https://play.google.com/store/apps/details?id=com.wireguard.android

        2. Купите подписку на {SERVICE_NAME}.

        3. После оплаты, вам придет сообщение с файлом, который нужно
        импортировать в приложении для подключения.

        Приятного пользования!
        """,
        reply_markup=home_kb(),
    )


@invoices_router.pre_checkout_query(F.invoice_payload == "demo")
async def pre_checkout_query(query: PreCheckoutQuery) -> None:
    """
    Pre-checkout query handler
    """
    await query.answer(ok=True)


@invoices_router.pre_checkout_query(F.invoice_payload == "real")
async def pre_checkout_query(query: PreCheckoutQuery) -> None:
    """
    Pre-checkout query handler
    """
    if ccy["currency"] == (query.invoice_payload) and ccy["currency_value"] > 90:
        await query.answer(ok=True)
    else:
        await query.answer(
            ok=False, error_message="Невозможно купить подписку, повторите позже."
        )


@invoices_router.callback_query(F.data.startswith("home"))
async def home_menu(call: CallbackQuery) -> None:
    """
    returns user to the home menu
    """
    await call.message.answer(
        f"Вы готовы оформить подписку на {SERVICE_NAME}?",
        reply_markup=subscribe_management_kb(),
    )


@invoices_router.callback_query(F.data.startswith("accept"))
async def home_menu(call: CallbackQuery) -> None:
    """
    returns user to the home menu
    """
    await call.message.answer(
        f"Вы готовы оформить подписку на {SERVICE_NAME}?",
        reply_markup=subscribe_management_kb(),
    )


@invoices_router.message(Command("start"))
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    await message.answer(
        f"""Привет, {html.bold(message.from_user.full_name)}!
            Перед началом использования сервиса и оплаты,
            внимательно ознакомьтесь с инструкцией и правилами использования сервиса.

            Принимая условия сервиса, Вы признаете, что несете
            полную ответственность за использование сервиса.
            Подписка предоставляется на одно устройство.
            Возврат средств не предусмотрен за подписку на сервис,
            оплата происходит единоразово на 30 дней.
            При повторной оплате подписка продлевается на 30 дней.

            Принимаете условия использования сервиса?
        """,
        reply_markup=accept_kb(),
    )


async def main() -> None:
    """Initialize Bot instance with default bot properties which will be passed to all API calls"""
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp.include_router(invoices_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
