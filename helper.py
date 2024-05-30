import os
import aiosqlite
import asyncio


async def initialize_tables() -> aiosqlite.Connection:
    """
    Creates 1 table in the directory database.db,

    0 - roles_list:
        cols: GUILD_ID (int), ADMIN_ID (int), TESTER_ID (int), LT5_ID (int), HT5_ID (int), LT4_ID (int), HT4_ID (int), LT3_ID (int), HT3_ID (int), LT2_ID (int), HT2_ID (int), LT1_ID (int), HT1_ID (int)
    """
    db_path = os.path.join(os.path.dirname(__file__), "database.db")
    db = await aiosqlite.connect(db_path)
    await db.execute(
        """
    CREATE TABLE IF NOT EXISTS roles_list (
        Guild_ID int PRIMARY_KEY,
        Admin_ID int,
        Tester_ID int,
        LT5_ID int,
        HT5_ID int,
        LT4_ID int,
        HT4_ID int,
        LT3_ID int,
        HT3_ID int,
        LT2_ID int,
        HT2_ID int,
        LT1_ID int,
        HT1_ID int
    );
    """
    )
    await db.commit()
    return db


async def get_rank_id(db: aiosqlite.Connection, guild_id: int, rank_name: str) -> int:
    rank_col = rank_name.strip().title().replace("Lt", "LT").replace("Ht", "HT") + "_ID"

    cursor = await db.execute(
        f"""
    SELECT {rank_col} FROM roles_list WHERE Guild_ID = {guild_id}
    """
    )
    res = await cursor.fetchone()

    return -1 if res == None else res[0]


async def get_all_tier_ids(db: aiosqlite.Connection, guild_id: int):
    cursor = await db.execute(
        f"""
    SELECT LT5_ID, HT5_ID, LT4_ID, HT4_ID, LT3_ID, HT3_ID, LT2_ID, HT2_ID, LT1_ID, HT1_ID
    FROM roles_list
    WHERE Guild_ID = {guild_id}
    """
    )
    res = await cursor.fetchall()
    return res[0]


async def main():
    # For testing only
    db = await initialize_tables()
    id = await get_rank_id(db, 1230836040588071004, "Tester")
    all_tier_ids = await get_all_tier_ids(db, 1230836040588071004)
    print(id)
    print(all_tier_ids)


if __name__ == "__main__":
    asyncio.run(main())
