import asyncio

from sqlalchemy import text

from app.db.session import AsyncSessionLocal


async def test_connection():
    print("Starting database connection test...")

    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT 1"))
        print("Database connection successful:", result.scalar())


if __name__ == "__main__":
    asyncio.run(test_connection())