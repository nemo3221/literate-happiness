import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from market import get_top_gifts, get_gift_price, get_market_stats
from alerts import alert_manager
from database import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


def main_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Рынок сейчас", callback_data="market"),
            InlineKeyboardButton(text="🔥 Топ подарков", callback_data="top"),
        ],
        [
            InlineKeyboardButton(text="🚨 Мои алерты", callback_data="alerts"),
            InlineKeyboardButton(text="➕ Добавить алерт", callback_data="add_alert"),
        ],
        [
            InlineKeyboardButton(text="📈 Аналитика", callback_data="analytics"),
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings"),
        ],
    ])
    return keyboard


@dp.message(Command("start"))
async def cmd_start(message: Message):
    await db.add_user(message.from_user.id)
    text = (
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "🤖 Я бот для анализа рынка NFT подарков в Telegram.\n\n"
        "💡 Что я умею:\n"
        "• 📊 Отслеживать цены подарков в реальном времени\n"
        "• 🚨 Присылать сигналы когда выгодно покупать/продавать\n"
        "• 📈 Показывать аналитику и тренды рынка\n"
        "• 🔔 Настраивать персональные алерты\n\n"
        "Выбери что тебя интересует 👇"
    )
    await message.answer(text, reply_markup=main_menu())


@dp.message(Command("menu"))
async def cmd_menu(message: Message):
    await message.answer("Главное меню 👇", reply_markup=main_menu())


@dp.callback_query(lambda c: c.data == "market")
async def show_market(callback: CallbackQuery):
    await callback.answer("Загружаю данные рынка...")
    stats = await get_market_stats()
    text = (
        "📊 *Рынок NFT подарков — сейчас*\n\n"
        f"💰 Общий объём за 24ч: `{stats['volume_24h']}` TON\n"
        f"📦 Активных листингов: `{stats['listings']}`\n"
        f"📈 Средняя цена: `{stats['avg_price']}` TON\n"
        f"🔥 Сделок за 24ч: `{stats['trades_24h']}`\n\n"
        f"📉 Минимальная цена: `{stats['floor_price']}` TON\n"
        f"📈 Тренд: {stats['trend']}\n\n"
        f"🕐 Обновлено: {stats['updated']}"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="market")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_main")],
    ])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)


@dp.callback_query(lambda c: c.data == "top")
async def show_top(callback: CallbackQuery):
    await callback.answer("Загружаю топ подарков...")
    gifts = await get_top_gifts(limit=10)
    
    text = "🔥 *Топ-10 подарков по объёму торгов*\n\n"
    for i, gift in enumerate(gifts, 1):
        change = gift['change_24h']
        emoji = "📈" if change > 0 else "📉" if change < 0 else "➡️"
        text += (
            f"{i}. *{gift['name']}*\n"
            f"   💰 {gift['price']} TON  {emoji} {change:+.1f}%\n"
            f"   📦 Листингов: {gift['listings']}\n\n"
        )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📈 По росту", callback_data="top_gainers"),
            InlineKeyboardButton(text="📉 По падению", callback_data="top_losers"),
        ],
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="top")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_main")],
    ])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)


@dp.callback_query(lambda c: c.data == "top_gainers")
async def show_top_gainers(callback: CallbackQuery):
    await callback.answer("Загружаю растущие...")
    gifts = await get_top_gifts(limit=10, sort_by="gainers")
    
    text = "📈 *Топ растущих подарков за 24ч*\n\n"
    for i, gift in enumerate(gifts, 1):
        text += (
            f"{i}. *{gift['name']}*\n"
            f"   💰 {gift['price']} TON  📈 +{gift['change_24h']:.1f}%\n\n"
        )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="top")],
    ])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)


@dp.callback_query(lambda c: c.data == "top_losers")
async def show_top_losers(callback: CallbackQuery):
    await callback.answer("Загружаю падающие...")
    gifts = await get_top_gifts(limit=10, sort_by="losers")
    
    text = "📉 *Топ падающих подарков за 24ч*\n\n"
    for i, gift in enumerate(gifts, 1):
        text += (
            f"{i}. *{gift['name']}*\n"
            f"   💰 {gift['price']} TON  📉 {gift['change_24h']:.1f}%\n\n"
        )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="top")],
    ])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)


@dp.callback_query(lambda c: c.data == "alerts")
async def show_alerts(callback: CallbackQuery):
    user_alerts = await db.get_user_alerts(callback.from_user.id)
    
    if not user_alerts:
        text = (
            "🚨 *Мои алерты*\n\n"
            "У тебя пока нет алертов.\n\n"
            "Добавь алерт чтобы получать уведомления когда:\n"
            "• Цена подарка упадёт до нужного уровня\n"
            "• Появится выгодная возможность для покупки\n"
            "• Объём торгов резко вырастет"
        )
    else:
        text = "🚨 *Мои алерты*\n\n"
        for alert in user_alerts:
            status = "✅" if alert['active'] else "⏸️"
            text += f"{status} *{alert['gift_name']}* — {alert['condition']} {alert['price']} TON\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить алерт", callback_data="add_alert")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_main")],
    ])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)


@dp.callback_query(lambda c: c.data == "add_alert")
async def add_alert(callback: CallbackQuery):
    text = (
        "➕ *Добавить алерт*\n\n"
        "Напиши мне в формате:\n"
        "`/alert Название_подарка ниже 5.5`\n\n"
        "Примеры:\n"
        "`/alert Дерево ниже 3.0`\n"
        "`/alert Торт выше 10.0`\n\n"
        "Я пришлю уведомление как только цена достигнет нужного уровня! 🔔"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="alerts")],
    ])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)


@dp.message(Command("alert"))
async def cmd_alert(message: Message):
    parts = message.text.split()
    if len(parts) < 4:
        await message.answer(
            "❌ Неверный формат.\n\n"
            "Используй: `/alert Название ниже 5.5`",
            parse_mode="Markdown"
        )
        return
    
    gift_name = parts[1]
    condition = parts[2]  # ниже / выше
    try:
        price = float(parts[3])
    except ValueError:
        await message.answer("❌ Цена должна быть числом, например `5.5`", parse_mode="Markdown")
        return
    
    await db.add_alert(message.from_user.id, gift_name, condition, price)
    await message.answer(
        f"✅ Алерт добавлен!\n\n"
        f"🎁 Подарок: *{gift_name}*\n"
        f"📊 Условие: цена {condition} *{price} TON*\n\n"
        f"Пришлю уведомление как только условие сработает! 🔔",
        parse_mode="Markdown"
    )


@dp.callback_query(lambda c: c.data == "analytics")
async def show_analytics(callback: CallbackQuery):
    text = (
        "📈 *Аналитика рынка*\n\n"
        "🔜 Скоро здесь появятся:\n\n"
        "• 📊 Графики цен (7д / 30д)\n"
        "• 💡 Сигналы покупки/продажи\n"
        "• 🏆 Самые прибыльные подарки\n"
        "• 💰 ROI калькулятор\n"
        "• 🤖 Авто-торговля\n\n"
        "_Разрабатывается в следующих обновлениях..._"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_main")],
    ])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)


@dp.callback_query(lambda c: c.data == "settings")
async def show_settings(callback: CallbackQuery):
    text = (
        "⚙️ *Настройки*\n\n"
        "🔔 Уведомления: *Включены*\n"
        "💰 Валюта: *TON*\n"
        "🕐 Частота обновления: *5 минут*\n"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_main")],
    ])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)


@dp.callback_query(lambda c: c.data == "back_main")
async def back_main(callback: CallbackQuery):
    await callback.message.edit_text("Главное меню 👇", reply_markup=main_menu())


async def price_monitor():
    """Фоновая задача — мониторинг цен и отправка алертов"""
    while True:
        try:
            triggered = await alert_manager.check_alerts()
            for alert in triggered:
                await bot.send_message(
                    alert['user_id'],
                    f"🚨 *АЛЕРТ СРАБОТАЛ!*\n\n"
                    f"🎁 *{alert['gift_name']}*\n"
                    f"💰 Текущая цена: *{alert['current_price']} TON*\n"
                    f"📊 Условие: цена {alert['condition']} {alert['target_price']} TON\n\n"
                    f"⚡ Действуй быстро!",
                    parse_mode="Markdown"
                )
        except Exception as e:
            logger.error(f"Monitor error: {e}")
        
        await asyncio.sleep(300)  # Проверка каждые 5 минут


async def main():
    await db.init()
    asyncio.create_task(price_monitor())
    logger.info("🤖 Бот запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
