import aiosqlite
import time

from bot.config import settings

_db: aiosqlite.Connection | None = None


async def get_db() -> aiosqlite.Connection:
    global _db
    if _db is None:
        _db = await aiosqlite.connect(settings.db_path)
        _db.row_factory = aiosqlite.Row
        await _init_tables(_db)
    return _db


async def _init_tables(db: aiosqlite.Connection) -> None:
    await db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            created_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            input_type TEXT NOT NULL,  -- photo / text / url
            result_color TEXT,         -- red / yellow / green
            created_at REAL NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            cta_type TEXT NOT NULL,    -- sign / lawyer / website
            created_at REAL NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
    """)
    await db.commit()
    # Migration: add input_data column to checks if missing
    try:
        await db.execute("ALTER TABLE checks ADD COLUMN input_data TEXT")
        await db.commit()
    except Exception:
        pass  # column already exists


async def ensure_user(user_id: int, username: str | None, first_name: str | None) -> None:
    db = await get_db()
    await db.execute(
        "INSERT OR IGNORE INTO users (user_id, username, first_name, created_at) VALUES (?, ?, ?, ?)",
        (user_id, username, first_name, time.time()),
    )
    await db.commit()


async def save_check(user_id: int, input_type: str, result_color: str | None, input_data: str | None = None) -> None:
    db = await get_db()
    await db.execute(
        "INSERT INTO checks (user_id, input_type, result_color, created_at, input_data) VALUES (?, ?, ?, ?, ?)",
        (user_id, input_type, result_color, time.time(), input_data),
    )
    await db.commit()


async def save_lead(user_id: int, cta_type: str) -> None:
    db = await get_db()
    await db.execute(
        "INSERT INTO leads (user_id, cta_type, created_at) VALUES (?, ?, ?)",
        (user_id, cta_type, time.time()),
    )
    await db.commit()


async def count_recent_checks(user_id: int, window_seconds: int = 60) -> int:
    db = await get_db()
    cursor = await db.execute(
        "SELECT COUNT(*) FROM checks WHERE user_id = ? AND created_at > ?",
        (user_id, time.time() - window_seconds),
    )
    row = await cursor.fetchone()
    return row[0] if row else 0


async def count_total_checks(user_id: int) -> int:
    db = await get_db()
    cursor = await db.execute(
        "SELECT COUNT(*) FROM checks WHERE user_id = ?",
        (user_id,),
    )
    row = await cursor.fetchone()
    return row[0] if row else 0


async def get_setting(key: str) -> str | None:
    db = await get_db()
    cursor = await db.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = await cursor.fetchone()
    return row[0] if row else None


async def set_setting(key: str, value: str) -> None:
    db = await get_db()
    await db.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )
    await db.commit()


async def delete_setting(key: str) -> None:
    db = await get_db()
    await db.execute("DELETE FROM settings WHERE key = ?", (key,))
    await db.commit()


async def get_all_settings() -> dict[str, str]:
    db = await get_db()
    cursor = await db.execute("SELECT key, value FROM settings")
    rows = await cursor.fetchall()
    return {row[0]: row[1] for row in rows}


async def close_db() -> None:
    global _db
    if _db is not None:
        await _db.close()
        _db = None
