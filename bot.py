import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo, ReplyKeyboardMarkup, KeyboardButton

TOKEN = "8653037606:AAGoHdiKVa8GSrttDJfE0xDhxy06icpb-qA" # <-- ВСТАВЬ ТОКЕН СЮДА
URL = "https://literate-happiness-flax.vercel.app/"

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: types.Message):
    # Создаем кнопку Mini App
    kb = [
        [KeyboardButton(text="🚀 ОТКРЫТЬ FLIPPER", web_app=WebAppInfo(url=URL))]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    
    await message.answer(
        f"Привет, {message.from_user.full_name}! 👋\n\n"
        "Добро пожаловать в элитный Flipper App.\n"
        "Нажми кнопку ниже, чтобы войти.",
        reply_markup=keyboard
    )

async def main():
    print("Бот запущен и ждет нажатия /start...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
