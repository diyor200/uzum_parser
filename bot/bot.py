import asyncio
import json
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
from aiogram.types import Message, FSInputFile

# Bot token can be obtained via https://t.me/BotFather
TOKEN = "7274490167:AAFlQOx1U4BNcwe-3uJ8D6H7ZYwpkTrwI8c"

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
    if resp.status_code != 200:
        await message.answer(f"parsing serviceda muammo yuzaga keldi!\n{resp.text=}")
        await state.clear()
        return

    data = resp.json()
    # Serialize JSON compactly
    json_text = json.dumps(data, indent=2, ensure_ascii=False)

    if len(json_text) > 4000:
        # If too long, send as a file
        with open("parsed_product.json", "w", encoding="utf-8") as f:
            f.write(json_text)
        await message.answer_document(FSInputFile("parsed_product.json"))
    else:
        # Otherwise send directly
        await message.answer(f"<pre>{json_text}</pre>", parse_mode="HTML")
    # product = data.get("data", {})
    # text = (
    #     f"<b>{product.get('title')}</b>\n"
    #     f"⭐️:️ Reyting: {product.get('rating')}\n"
    #     f"💡: Chegirma: {product.get('discount')}\n"
    #     f"💸: Narx:\n\tUzum kartasi bilan to'lansa: {product.get('with_uzum_card_price')} so'm\n\tBoshqa karta bilan to'lansa: {product.get('with_another_card_price')}\n"
    #     f"🏬: Sotuvchi: {product['seller']['title']} (⭐️:️ {product['seller']['rating']})\n"
    #     f"🛍: Sotuvlar soni (hafta): {product.get('sold_count')}\n\n"
    #     "<b>📏: O'lchamlar va mavjud soni:</b>\n"
    # )
    # for item in product.get("products", []):
    #     text += f"• {item['size']} — {item['available_count']} dona\n"
    # images = product.get("images", [])
    # if images:
    #     text += "\n<b>🖼: Rasm URL'lari:</b>\n"
    #     text += "\n".join(images)
    #
    # await message.answer(text=text)
    await state.clear()

async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())