import aiohttp
import random
from datetime import datetime


# Список реальных подарков Telegram
GIFT_NAMES = [
    "Plush Pepe", "Homemade Cake", "Lol Pop", "Love Potion",
    "Berry Box", "Jelly Bunny", "Witch Hat", "Evil Eye",
    "Kissed Frog", "Perfume Bottle", "Sakura", "Desk Calendar",
    "Eternal Rose", "Toy Bear", "Cookie Heart", "Star Notepad",
    "Genie Lamp", "Vintage Cigar", "Spy Agaric", "Electric Skull",
]


async def fetch_fragment_data():
    """
    Получение данных с Fragment.com
    Fragment не имеет публичного API, поэтому используем
    веб-скрапинг или моковые данные для демонстрации.
    В реальном боте нужно подключить платный API или парсер.
    """
    # TODO: Подключить реальный источник данных
    # Варианты:
    # 1. Getgems GraphQL API: https://getgems.io/graphql
    # 2. Tonapi.io: https://tonapi.io/
    # 3. Парсинг Fragment.com через playwright
    
    return None


def generate_mock_gift(name: str):
    """Генерация реалистичных тестовых данных"""
    base_price = random.uniform(1.5, 50.0)
    change = random.uniform(-15.0, 20.0)
    
    return {
        "name": name,
        "price": round(base_price, 2),
        "change_24h": round(change, 1),
        "listings": random.randint(5, 500),
        "volume_24h": round(base_price * random.randint(10, 200), 1),
        "trades_24h": random.randint(5, 150),
    }


async def get_top_gifts(limit: int = 10, sort_by: str = "volume"):
    """Получить топ подарков"""
    gifts = [generate_mock_gift(name) for name in GIFT_NAMES]
    
    if sort_by == "gainers":
        gifts = [g for g in gifts if g['change_24h'] > 0]
        gifts.sort(key=lambda x: x['change_24h'], reverse=True)
    elif sort_by == "losers":
        gifts = [g for g in gifts if g['change_24h'] < 0]
        gifts.sort(key=lambda x: x['change_24h'])
    else:
        gifts.sort(key=lambda x: x['volume_24h'], reverse=True)
    
    return gifts[:limit]


async def get_gift_price(gift_name: str) -> float:
    """Получить текущую цену конкретного подарка"""
    gift = generate_mock_gift(gift_name)
    return gift['price']


async def get_market_stats():
    """Общая статистика рынка"""
    gifts = [generate_mock_gift(name) for name in GIFT_NAMES]
    
    total_volume = sum(g['volume_24h'] for g in gifts)
    total_listings = sum(g['listings'] for g in gifts)
    total_trades = sum(g['trades_24h'] for g in gifts)
    avg_price = sum(g['price'] for g in gifts) / len(gifts)
    floor_price = min(g['price'] for g in gifts)
    
    # Определяем тренд рынка
    gainers = sum(1 for g in gifts if g['change_24h'] > 0)
    if gainers > len(gifts) * 0.6:
        trend = "📈 Бычий (растущий)"
    elif gainers < len(gifts) * 0.4:
        trend = "📉 Медвежий (падающий)"
    else:
        trend = "➡️ Боковой (нейтральный)"
    
    return {
        "volume_24h": round(total_volume, 1),
        "listings": total_listings,
        "avg_price": round(avg_price, 2),
        "trades_24h": total_trades,
        "floor_price": round(floor_price, 2),
        "trend": trend,
        "updated": datetime.now().strftime("%H:%M:%S"),
    }
