import time
from bot.db import get_db


async def get_summary() -> dict:
    db = await get_db()

    cur = await db.execute("SELECT COUNT(*) FROM users")
    total_users = (await cur.fetchone())[0]

    cur = await db.execute("SELECT COUNT(*) FROM checks")
    total_checks = (await cur.fetchone())[0]

    cur = await db.execute("SELECT COUNT(*) FROM leads")
    total_leads = (await cur.fetchone())[0]

    conversion = (total_leads / total_checks * 100) if total_checks > 0 else 0

    return {
        "total_users": total_users,
        "total_checks": total_checks,
        "total_leads": total_leads,
        "conversion": round(conversion, 1),
    }


async def get_users_by_day(days: int = 30) -> list[dict]:
    db = await get_db()
    since = time.time() - days * 86400
    cur = await db.execute(
        """
        SELECT date(created_at, 'unixepoch') as day, COUNT(*) as cnt
        FROM users WHERE created_at >= ?
        GROUP BY day ORDER BY day
        """,
        (since,),
    )
    return [{"day": r[0], "count": r[1]} for r in await cur.fetchall()]


async def get_checks_by_day(days: int = 30) -> list[dict]:
    db = await get_db()
    since = time.time() - days * 86400
    cur = await db.execute(
        """
        SELECT date(created_at, 'unixepoch') as day, COUNT(*) as cnt
        FROM checks WHERE created_at >= ?
        GROUP BY day ORDER BY day
        """,
        (since,),
    )
    return [{"day": r[0], "count": r[1]} for r in await cur.fetchall()]


async def get_checks_by_type() -> list[dict]:
    db = await get_db()
    cur = await db.execute(
        "SELECT input_type, COUNT(*) as cnt FROM checks GROUP BY input_type"
    )
    return [{"type": r[0], "count": r[1]} for r in await cur.fetchall()]


async def get_checks_by_color() -> list[dict]:
    db = await get_db()
    cur = await db.execute(
        "SELECT result_color, COUNT(*) as cnt FROM checks GROUP BY result_color"
    )
    return [{"color": r[0], "count": r[1]} for r in await cur.fetchall()]


async def get_leads_by_type() -> list[dict]:
    db = await get_db()
    cur = await db.execute(
        "SELECT cta_type, COUNT(*) as cnt FROM leads GROUP BY cta_type"
    )
    return [{"type": r[0], "count": r[1]} for r in await cur.fetchall()]


async def get_recent_users(limit: int = 50, offset: int = 0) -> list[dict]:
    db = await get_db()
    cur = await db.execute(
        """
        SELECT user_id, username, first_name,
               datetime(created_at, 'unixepoch') as created
        FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?
        """,
        (limit, offset),
    )
    return [dict(r) for r in await cur.fetchall()]


async def get_recent_checks(
    limit: int = 50, offset: int = 0,
    input_type: str | None = None, result_color: str | None = None,
) -> list[dict]:
    db = await get_db()
    query = """
        SELECT c.id, c.user_id, u.username, c.input_type, c.result_color,
               datetime(c.created_at, 'unixepoch') as created
        FROM checks c LEFT JOIN users u ON c.user_id = u.user_id
    """
    params: list = []
    wheres: list[str] = []
    if input_type:
        wheres.append("c.input_type = ?")
        params.append(input_type)
    if result_color:
        wheres.append("c.result_color = ?")
        params.append(result_color)
    if wheres:
        query += " WHERE " + " AND ".join(wheres)
    query += " ORDER BY c.created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    cur = await db.execute(query, params)
    return [dict(r) for r in await cur.fetchall()]


async def get_recent_leads(
    limit: int = 50, offset: int = 0, cta_type: str | None = None,
) -> list[dict]:
    db = await get_db()
    query = """
        SELECT l.id, l.user_id, u.username, l.cta_type,
               datetime(l.created_at, 'unixepoch') as created,
               (SELECT c.input_type FROM checks c
                WHERE c.user_id = l.user_id AND c.created_at <= l.created_at
                ORDER BY c.created_at DESC LIMIT 1) as last_check_type,
               (SELECT c.result_color FROM checks c
                WHERE c.user_id = l.user_id AND c.created_at <= l.created_at
                ORDER BY c.created_at DESC LIMIT 1) as last_check_color,
               (SELECT c.input_data FROM checks c
                WHERE c.user_id = l.user_id AND c.created_at <= l.created_at
                ORDER BY c.created_at DESC LIMIT 1) as last_check_data
        FROM leads l LEFT JOIN users u ON l.user_id = u.user_id
    """
    params: list = []
    if cta_type:
        query += " WHERE l.cta_type = ?"
        params.append(cta_type)
    query += " ORDER BY l.created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    cur = await db.execute(query, params)
    return [dict(r) for r in await cur.fetchall()]


async def count_users() -> int:
    db = await get_db()
    cur = await db.execute("SELECT COUNT(*) FROM users")
    return (await cur.fetchone())[0]


async def count_checks(
    input_type: str | None = None, result_color: str | None = None,
) -> int:
    db = await get_db()
    query = "SELECT COUNT(*) FROM checks"
    params: list = []
    wheres: list[str] = []
    if input_type:
        wheres.append("input_type = ?")
        params.append(input_type)
    if result_color:
        wheres.append("result_color = ?")
        params.append(result_color)
    if wheres:
        query += " WHERE " + " AND ".join(wheres)
    cur = await db.execute(query, params)
    return (await cur.fetchone())[0]


async def count_leads(cta_type: str | None = None) -> int:
    db = await get_db()
    query = "SELECT COUNT(*) FROM leads"
    params: list = []
    if cta_type:
        query += " WHERE cta_type = ?"
        params.append(cta_type)
    cur = await db.execute(query, params)
    return (await cur.fetchone())[0]
