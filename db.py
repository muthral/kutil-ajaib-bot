import os
import asyncio
import asyncpg
from typing import Optional, Dict, Any, List

_raw_url = os.environ.get("DATABASE_URL", "")
DATABASE_URL = _raw_url.replace("postgres://", "postgresql://", 1) if _raw_url.startswith("postgres://") else _raw_url

_pool: Optional[asyncpg.Pool] = None

async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=10)
    return _pool

async def close_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None

# -------------------- Wallet --------------------
async def db_get_wallet(user_id: int) -> Optional[Dict[str, Any]]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT user_id, name, saldo FROM wallet WHERE user_id = $1",
            user_id
        )
        if row:
            return {"user_id": row["user_id"], "name": row["name"], "saldo": row["saldo"]}
        return None

async def db_get_wallet_by_name(name: str) -> Optional[Dict[str, Any]]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT user_id, name, saldo FROM wallet WHERE name = $1 AND user_id <= 0",
            name
        )
        if row:
            return {"user_id": row["user_id"], "name": row["name"], "saldo": row["saldo"]}
        return None

async def db_get_wallet_by_any_name(name: str) -> Optional[Dict[str, Any]]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT user_id, name, saldo FROM wallet WHERE LOWER(name) = LOWER($1) LIMIT 1",
            name
        )
        if row:
            return {"user_id": row["user_id"], "name": row["name"], "saldo": row["saldo"]}
        return None

async def db_update_saldo(user_id: int, delta: int) -> Optional[int]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "UPDATE wallet SET saldo = saldo + $1 WHERE user_id = $2 RETURNING saldo",
            delta, user_id
        )
        return row["saldo"] if row else None

async def db_transfer_saldo(from_uid: int, to_uid: int, amount: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            row_from = await conn.fetchrow(
                "UPDATE wallet SET saldo = saldo - $1 WHERE user_id = $2 AND saldo >= $1 RETURNING saldo",
                amount, from_uid
            )
            if row_from is None:
                raise ValueError("saldo_kurang")
            row_to = await conn.fetchrow(
                "UPDATE wallet SET saldo = saldo + $1 WHERE user_id = $2 RETURNING saldo",
                amount, to_uid
            )
            if row_to is None:
                raise ValueError("target_not_found")
            return row_from["saldo"], row_to["saldo"]

async def db_delete_wallet(user_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM wallet WHERE user_id = $1", user_id)

async def db_set_wallet(user_id: int, name: str, saldo: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO wallet (user_id, name, saldo)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id) DO UPDATE SET
                name = EXCLUDED.name,
                saldo = EXCLUDED.saldo
            """,
            user_id, name, saldo
        )

async def db_get_all_wallets() -> List[Dict[str, Any]]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT user_id, name, saldo FROM wallet ORDER BY saldo DESC")
        return [{"user_id": r["user_id"], "name": r["name"], "saldo": r["saldo"]} for r in rows]

# -------------------- Badges --------------------
async def db_get_badges(user_id: int) -> List[str]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT badges FROM user_badges WHERE user_id = $1",
            user_id
        )
        if row and row["badges"]:
            return row["badges"]
        return []

async def db_set_badges(user_id: int, badges: List[str]):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO user_badges (user_id, badges)
            VALUES ($1, $2)
            ON CONFLICT (user_id) DO UPDATE SET
                badges = EXCLUDED.badges
            """,
            user_id, badges
        )

# -------------------- Scores --------------------
async def db_get_scores(chat_id: int) -> Dict[int, Dict[str, Any]]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT user_id, name, score FROM scores WHERE chat_id = $1",
            chat_id
        )
        result = {}
        for r in rows:
            result[r["user_id"]] = {"name": r["name"], "score": r["score"]}
        return result

async def db_set_score(chat_id: int, user_id: int, name: str, score: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO scores (chat_id, user_id, name, score)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (chat_id, user_id) DO UPDATE SET
                name = EXCLUDED.name,
                score = EXCLUDED.score
            """,
            chat_id, user_id, name, score
        )

async def db_get_all_scores(chat_id: int) -> List[Dict[str, Any]]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT user_id, name, score FROM scores WHERE chat_id = $1 ORDER BY score DESC",
            chat_id
        )
        return [{"user_id": r["user_id"], "name": r["name"], "score": r["score"]} for r in rows]

