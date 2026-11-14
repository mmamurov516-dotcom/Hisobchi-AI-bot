import aiosqlite
from datetime import datetime
from config import DB_PATH

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                full_name TEXT,
                username TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL, -- 'income' yoki 'expense'
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                raw_message TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        await db.commit()

async def register_user(user_id: int, full_name: str = "", username: str = ""):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (user_id, full_name, username)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                full_name = excluded.full_name,
                username = excluded.username
        """, (user_id, full_name, username))
        await db.commit()

async def add_transactions(user_id: int, items: list[dict], raw_message: str = "") -> list[dict]:
    saved_items = []
    async with aiosqlite.connect(DB_PATH) as db:
        for item in items:
            t_type = item.get("type", "expense").lower()
            category = item.get("category", "Boshqa")
            desc = item.get("description", "Noma'lum")
            amount = float(item.get("amount", 0))

            if amount <= 0:
                continue

            cursor = await db.execute("""
                INSERT INTO transactions (user_id, type, category, description, amount, raw_message)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, t_type, category, desc, amount, raw_message))
            
            saved_items.append({
                "id": cursor.lastrowid,
                "type": t_type,
                "category": category,
                "description": desc,
                "amount": amount
            })

        await db.commit()
    return saved_items

async def get_financial_summary(user_id: int) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT 
                COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0) AS total_income,
                COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0) AS total_expense,
                COUNT(CASE WHEN type = 'income' THEN 1 END) AS income_count,
                COUNT(CASE WHEN type = 'expense' THEN 1 END) AS expense_count
            FROM transactions
            WHERE user_id = ?
        """, (user_id,)) as cursor:
            row = await cursor.fetchone()
            total_income = row[0] if row else 0.0
            total_expense = row[1] if row else 0.0
            income_count = row[2] if row else 0
            expense_count = row[3] if row else 0

    balance = total_income - total_expense
    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": balance,
        "income_count": income_count,
        "expense_count": expense_count
    }

async def get_detailed_expenses(user_id: int, limit: int = 30) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT id, type, category, description, amount, timestamp
            FROM transactions
            WHERE user_id = ? AND type = 'expense'
            ORDER BY id DESC
            LIMIT ?
        """, (user_id, limit)) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def get_today_expenses(user_id: int) -> list[dict]:
    today = datetime.now().strftime("%Y-%m-%d")
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT id, type, category, description, amount, timestamp
            FROM transactions
            WHERE user_id = ? AND type = 'expense' AND date(timestamp) = date('now', 'localtime')
            ORDER BY id ASC
        """, (user_id,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def get_category_summary(user_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT category, SUM(amount) AS total_amount, COUNT(*) AS count
            FROM transactions
            WHERE user_id = ? AND type = 'expense'
            GROUP BY category
            ORDER BY total_amount DESC
        """, (user_id,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def delete_last_transaction(user_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT id, type, category, description, amount, timestamp
            FROM transactions
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 1
        """, (user_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            
            tx = dict(row)
            await db.execute("DELETE FROM transactions WHERE id = ?", (tx["id"],))
            await db.commit()
            return tx

async def clear_user_data(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM transactions WHERE user_id = ?", (user_id,))
        await db.commit()
