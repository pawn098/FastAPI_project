from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase


engine = create_async_engine('postgresql+asyncpg://ecommerce:XXXXXX@localhost:5432/ecommerce',
                             echo=True, pool_timeout=30,
                             connect_args={"command_timeout": 60},
                             max_overflow=5)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

class Base(DeclarativeBase):
    pass