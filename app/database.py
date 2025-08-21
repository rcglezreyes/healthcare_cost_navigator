import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://msuser:mspass@localhost:5432/msdrg")
engine = create_async_engine(DATABASE_URL, echo=False, pool_size=10, max_overflow=20)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def get_session():
    async with SessionLocal() as session:
        yield session
