import asyncio
import asyncpg
import os

_raw_url = os.environ.get("DATABASE_URL", "")
if not _raw_url:
    raise ValueError("DATABASE_URL tidak diset. Pastikan environment variable sudah diisi.")
DATABASE_URL = _raw_url.replace("postgres://", "postgresql://", 1) if _raw_url.startswith("postgres://") else _raw_url

# (name, saldo, badges)
INITIAL_DATA = [
    ("@pemudakhongguan", 12_615_000, []),
    ("@camelliabr",      11_255_000, []),
    ("@lvwonhan",         5_505_000, []),
    ("@badtinnitus",      5_425_000, ["🪽"]),
    ("@cepetanlulus",     5_295_000, []),
    ("@Lailight",         2_800_000, []),
    ("@samvwel",          2_270_000, ["🪽"]),
    ("@linkdivio",        2_030_000, []),
    ("@llaolyd",             95_000, []),
    ("@furabantartika",      50_000, []),
    ("@Vxrtle",              40_000, []),
    ("@Emyuihiy",            25_000, []),
    ("@tiramisuacaii",     -120_000, []),
]

async def create_tables(conn):
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS wallet (
            user_id BIGINT PRIMARY KEY,
            name TEXT NOT NULL,
            saldo INTEGER NOT NULL DEFAULT 100000
        )
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS user_badges (
            user_id BIGINT PRIMARY KEY,
            badges TEXT[] NOT NULL DEFAULT '{}'
        )
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            chat_id BIGINT,
            user_id BIGINT,
            name TEXT NOT NULL,
            score INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (chat_id, user_id)
        )
    """)

async def import_data():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await create_tables(conn)

        for i, (name, saldo, badges) in enumerate(INITIAL_DATA, start=1):
            placeholder_id = -i

            await conn.execute("""
                INSERT INTO wallet (user_id, name, saldo)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    saldo = EXCLUDED.saldo
            """, placeholder_id, name, saldo)

            if badges:
                await conn.execute("""
                    INSERT INTO user_badges (user_id, badges)
                    VALUES ($1, $2)
                    ON CONFLICT (user_id) DO UPDATE SET
                        badges = EXCLUDED.badges
                """, placeholder_id, badges)

            print(f"  ✅ {name} — saldo: {saldo:,}, badges: {badges if badges else '-'}")

        print("\n✅ Semua data berhasil diimpor!")
        print("Saat pemain pertama kali pakai bot, akun mereka otomatis terhubung ke data ini.")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(import_data())
