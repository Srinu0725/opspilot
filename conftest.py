
import pytest_asyncio

from app.db.session import engine


@pytest_asyncio.fixture(autouse=True)
async def dispose_async_engine_after_test():
    """Prevent pooled async connections from leaking between test event loops."""
    yield
    await engine.dispose()
