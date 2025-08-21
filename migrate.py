import os
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine

def split_sql(sql: str):
    parts = []
    cur = []
    for line in sql.splitlines():
        s = line.strip()
        if not s:
            continue
        cur.append(line)
        if s.endswith(";"):
            parts.append("\n".join(cur).rstrip(";").strip())
            cur = []
    if cur:
        parts.append("\n".join(cur).strip())
    return [p for p in parts if p]

async def run():
    url = os.getenv("DATABASE_URL", "")
    engine = create_async_engine(url, echo=False)
    async with engine.begin() as conn:
        for fname in ["migrations/001_init.sql", "migrations/002_indexes.sql"]:
            with open(fname, "r", encoding="utf-8") as f:
                sql = f.read()
            for stmt in split_sql(sql):
                await conn.exec_driver_sql(stmt)
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run())
