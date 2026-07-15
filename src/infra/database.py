from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.core.config import get_settings
from collections.abc import AsyncGenerator
settings = get_settings()
# 1. 创建引擎
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.APP_DEBUG,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True,
)


# 2.创建会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False, # 事务提交后，不自动过期
    class_=AsyncSession,
)

# 3. 定义异步获取数据库会话链接
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI Depends 注入, 自动提交和异常回滚"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e


