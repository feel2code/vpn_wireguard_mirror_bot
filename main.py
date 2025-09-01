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
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardMarkup,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

from db_tools import (
    check_subscription_end,
    get_obfuscated_user_conf,
    need_to_update_user,
)

logger = logging.getLogger(__name__)
invoices_router = Router(name=__name__)


load_dotenv(".env")
DEMO_REGIME = bool(int(getenv("DEMO_REGIME")))
SERVICE_NAME = getenv("SERVICE_NAME")
ADMIN = getenv("ADMIN")
TOKEN = getenv("BOT_TOKEN")
FS_USER = getenv("FS_USER")
HOST_AND_PORT = getenv("HOST_AND_PORT")

PRICING = {
    "vpn_30": int(getenv("VPN_30")),
    "proxy_30": int(getenv("PROXY_30")),
}
dp = Dispatcher()

if DEMO_REGIME:
    ccy = {
        "demo_1": {
            "payload": "demo_30",
            "value": 1,
        },
        "proxy_1": {
            "payload": "demo_proxy",
            "value": 1,
        },
    }
else:
    ccy = {
        "real_30": {
            "payload": "real_30",
            "value": PRICING["vpn_30"],
        },
        "real_60": {
            "payload": "real_60",
            "value": round(PRICING["vpn_30"] * 2 * 0.94),
        },
        "real_90": {
            "payload": "real_90",
            "value": round(PRICING["vpn_30"] * 3 * 0.9),
        },
        "proxy_30": {
            "payload": "proxy_30",
            "value": PRICING["proxy_30"],
        },
        "proxy_60": {
            "payload": "proxy_60",
            "value": round(PRICING["proxy_30"] * 2 * 0.94),
        },
        "proxy_90": {
            "payload": "proxy_90",
            "value": round(PRICING["proxy_30"] * 3 * 0.9),
        },
    }


def subscribe_management_kb() -> InlineKeyboardMarkup:
    """
    subscribe management keyboard
    """
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Купить подписку неVPN", callback_data="subscribe_vpn")
    kb.button(text="➕ Купить подписку PROXY", callback_data="subscribe_proxy")
    kb.button(text="ℹ️  Инструкция и поддержка", callback_data="instruction")
    kb.button(
        text="👽 Проверить подписку", callback_data="check_end_date_of_subscription"
    )
    kb.adjust(1, 1, 1, 1)
    return kb.as_markup()


def home_kb() -> InlineKeyboardMarkup:
    """
    home keyboard
    """
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Купить подписку неVPN", callback_data="subscribe_vpn")
    kb.button(text="➕ Купить подписку PROXY", callback_data="subscribe_proxy")
    kb.button(text="😢 Назад", callback_data="home")
    kb.adjust(1, 1, 1)
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
        vpn_check = check_subscription_end(call.from_user.id, is_proxy=0)
        proxy_check = check_subscription_end(call.from_user.id, is_proxy=1)
        if vpn_check:
            await call.message.answer(
                f"""Ваша подписка на неVPN действует до:
                {str(vpn_check)[:-7]}"""
            )
        if proxy_check:
            await call.message.answer(
                f"""Ваша подписка на PROXY действует до:
                {str(proxy_check)[:-7]}"""
            )
        return
    await call.message.answer(
        f"Действующие подписки на {SERVICE_NAME} не найдены!",
    )


@invoices_router.callback_query(F.data.startswith("subscribe_vpn"))
async def subscribe_vpn(call: CallbackQuery) -> None:
    """
    subscribe to the VPN service
    """
    for period in [30, 60, 90]:
        await call.message.answer_invoice(
            title="Приобрести подписку неVPN",
            description=f"Подписка на {period} дней на {SERVICE_NAME} неVPN",
            prices=[
                LabeledPrice(
                    label=ccy[f"real_{period}"]["payload"].title(),
                    amount=ccy[f"real_{period}"]["value"],
                ),
            ],
            payload=ccy[f"real_{period}"]["payload"],
            currency="XTR",
        )


@invoices_router.callback_query(F.data.startswith("subscribe_proxy"))
async def subscribe_proxy(call: CallbackQuery) -> None:
    """
    subscribe to the PROXY service
    """
    for period in [30, 60, 90]:
        await call.message.answer_invoice(
            title="Приобрести подписку PROXY",
            description=f"Подписка на {period} дней на {SERVICE_NAME} PROXY",
            prices=[
                LabeledPrice(
                    label=ccy[f"proxy_{period}"]["payload"].title(),
                    amount=ccy[f"proxy_{period}"]["value"],
                ),
            ],
            payload=ccy[f"proxy_{period}"]["payload"],
            currency="XTR",
        )


@invoices_router.message(F.successful_payment)
async def successful_payment(message: Message, bot: Bot) -> None:
    """
    Successful payment handler and create config file
    then send it to the user
    """
    user_id = message.from_user.id
    uuid_gen = str(uuid4())[:13]

    if DEMO_REGIME:
        await bot.refund_star_payment(
            user_id=message.from_user.id,
            telegram_payment_charge_id=message.successful_payment.telegram_payment_charge_id,
        )
        await message.answer("Demo. Your payment has been refunded.")
        need_to_update_user(
            user_id=user_id,
            obfuscated_user=f"{uuid_gen}",
            invoice_payload=message.successful_payment.invoice_payload,
        )
        return

    await message.answer(
        f"""Спасибо за покупку подписки на {SERVICE_NAME}!
        Ваш ID платежа: {message.successful_payment.telegram_payment_charge_id}""",
        message_effect_id="5104841245755180586",  # stars effect
    )
    if not need_to_update_user(
        user_id=user_id,
        obfuscated_user=f"{uuid_gen}",
        invoice_payload=message.successful_payment.invoice_payload,
    ):
        # PROXY
        if message.successful_payment.invoice_payload.startswith("proxy_"):
            proxy_key = str(uuid4())[:13]
            subprocess.run(
                shlex.split(
                    f"/{FS_USER}/vpn_wireguard_mirror_bot/./create_proxy.sh {uuid_gen} {proxy_key}"
                ),
                check=False,
            )
            await bot.send_message(
                chat_id=message.from_user.id,
                text=(
                    f"Хост: {HOST_AND_PORT}\nПользователь: {uuid_gen}\nПароль: {proxy_key}"
                ),
            )
            return
        # VPN
        if message.successful_payment.invoice_payload.startswith("real_"):
            subprocess.run(
                shlex.split(
                    f"/{FS_USER}/vpn_wireguard_mirror_bot/./create_config.sh {uuid_gen}"
                ),
                check=False,
            )
            await bot.send_document(
                chat_id=user_id,
                document=FSInputFile(f"/{FS_USER}/{uuid_gen}.conf"),
            )
            return

    await message.answer("Подписка продлена.")


@invoices_router.callback_query(F.data.startswith("instruction"))
async def get_instruction(call: CallbackQuery) -> None:
    """
    instruction for the service install
    """
    await call.message.answer(
        f"""
        Инструкция по установке неVPN:
        1. Установите приложение Wireguard на свой смартфон

        * Для iOS: https://apps.apple.com/us/app/wireguard/id1441195209
        * Для Android: https://play.google.com/store/apps/details?id=com.wireguard.android

        2. Купите подписку на {SERVICE_NAME}.

        3. После оплаты, вам придет сообщение с файлом, который нужно
        импортировать в приложении для подключения.

        Приятного пользования! Подписка на сервис не означает обхода блокировок,
        дает доступ к ресурсам компании {SERVICE_NAME}.

        По вопросам поддержки обращаться к @feel2code
        """.replace(
            "  ", ""
        ),
        reply_markup=home_kb(),
    )


@invoices_router.pre_checkout_query(F.invoice_payload)
async def pre_checkout_query(query: PreCheckoutQuery) -> None:
    """
    Pre-checkout query handler
    """
    if query.invoice_payload.startswith("real_"):
        await query.answer(ok=True)
        return
    if query.invoice_payload.startswith("proxy"):
        await query.answer(ok=True)
        return
    if query.invoice_payload.startswith("demo_"):
        await query.answer(ok=True)
        return
    await query.answer(ok=False, error_message="Начните работу с ботом заново. /start")


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
async def accept_call(call: CallbackQuery) -> None:
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

            Сервис {SERVICE_NAME} не предоставляет услуги VPN,
            а лишь помогает настроить доступ к ресурсам компании {SERVICE_NAME}.
            Сервис не предназначен для обхода блокировок и цензуры.
            Пользователь несет полную ответственность за использование сервиса.
            Сервис не хранит ваши персональные данные, и не обрабатывает их.
            Сервис не несет ответственности за использование сервиса в незаконных целях.
            Сервис шифрует трафик между вашим устройством и ресурсами компании {SERVICE_NAME}.

            В целях устранения недопонимания, доступ к ресурсам назван неVPN,
            и не является VPN сервисом.

            Принимая условия сервиса, Вы признаете, что несете
            полную ответственность за использование сервиса.
            Подписка предоставляется на одно устройство.
            Возврат средств не предусмотрен за подписку на сервис,
            оплата происходит единоразово на 30, 60 или 90 дней.
            При повторной оплате подписка продлевается.

            Также есть отдельная подписка на PROXY на 30, 60 или 90 дней.

            Принимаете условия использования сервиса?
        """.replace(
            "  ", ""
        ),
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
