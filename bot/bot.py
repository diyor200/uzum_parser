import asyncio
import logging
import sys
from os import getenv
import requests

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message

# Bot token can be obtained via https://t.me/BotFather
TOKEN = getenv("BOT_TOKEN")

# All handlers should be attached to the Router (or Dispatcher)

dp = Dispatcher()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    # Most event objects have aliases for API methods that can be called in events' context
    # For example if you want to answer to incoming message you can use `message.answer(...)` alias
    # and the target chat will be passed to :ref:`aiogram.methods.send_message.SendMessage`
    # method automatically or call API method directly via
    # Bot instance: `bot.send_message(chat_id=message.chat.id, ...)`
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}!")


class UrlState(StatesGroup):
    URL = State()

@dp.message(Command("parse"))
async def parser_handler(message: Message, state: FSMContext) -> None:
    await message.answer(
        text="product url ini yuboring:\n\nMisol:https://uzum.uz/uz/product/new-balance-erkaklar-krossovkalari-1552187"
    )
    await state.set_state(UrlState.URL)


@dp.message(UrlState.URL)
async def parser_handler(message: Message, state: FSMContext) -> None:
    url = message.text

    await message.answer("so'rov yuborilmoqda iltimos kutib turing...")
    resp = requests.post(url="http://scraper:8000/parse_product", json={"url": url})
    data = resp.json()

    product = data.get("data", {})
    text = (
        f"<b>{product.get('title')}</b>\n"
        f"⭐️:️ Reyting: {product.get('rating')}\n"
        f"💸: Narx: {product.get('price')} so'm {product.get('discount')}\n"
        f"🏬: Sotuuvchi: {product['seller']['title']} (:star:️ {product['seller']['rating']})\n"
        f"📦: Qolgan mahsulotlar: {product.get('available_amount')}\n"
        f"🛍: Sotuvlar soni (hafta): {product.get('sold_count')}\n\n"
        "<b>📏: O'lchamlar va mavjud soni:</b>\n"
    )
    for item in product.get("products", []):
        text += f"• {item['size']} — {item['available_count']} dona\n"
    images = product.get("images", [])
    if images:
        text += "\n<b>🖼: Rasm URL'lari:</b>\n"
        text += "\n".join(images)

    await message.answer(text=text)
    await state.clear()

async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())