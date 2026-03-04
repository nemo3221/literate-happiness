import aiosqlite
import os

DB_PATH = "bot_database.db"


class Database:
    def __init__(self):
        self.db_path = DB_PATH

    async def init(self):
        """Создать таблицы если не существуют"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notifications_on INTEGER DEFAULT 1
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    gift_name TEXT,
                    condition TEXT,
                    price REAL,
                    active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            await db.commit()

    async def add_user(self, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR IGNORE INTO users (user_id) VALUES (?)",
                (user_id,)
            )
            await db.commit()

    async def add_alert(self, user_id: int, gift_name: str, condition: str, price: float):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO alerts (user_id, gift_name, condition, price) VALUES (?, ?, ?, ?)",
                (user_id, gift_name, condition, price)
            )
            await db.commit()

    async def get_user_alerts(self, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM alerts WHERE user_id = ? AND active = 1",
                (user_id,)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_all_active_alerts(self):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM alerts WHERE active = 1"
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def deactivate_alert(self, alert_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE alerts SET active = 0 WHERE id = ?",
                (alert_id,)
            )
            await db.commit()


db = Database()
