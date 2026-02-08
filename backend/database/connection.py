import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from config import get_settings

logger = logging.getLogger("jingjin")
settings = get_settings()

engine = create_async_engine(settings.mysql_url, echo=False, pool_pre_ping=True)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db():
    """
    初始化數據庫表結構。
    使用 checkfirst=True（create_all 默認行為）：
    - 如果表已存在，跳過不覆蓋
    - 如果表不存在，自動建立
    """
    async with engine.begin() as conn:
        # 先檢查連接是否正常
        await conn.execute(text("SELECT 1"))
        logger.info("✓ MySQL 連接成功")

        # 獲取已有表
        existing = await conn.run_sync(
            lambda sync_conn: sync_conn.dialect.get_table_names(sync_conn)
        )
        if existing:
            logger.info(f"  已有數據表 ({len(existing)}): {', '.join(existing)}")
        else:
            logger.info("  數據庫為空，將建立所有表")

        # create_all 只會建立不存在的表，不會覆蓋已有表和數據
        await conn.run_sync(Base.metadata.create_all)

        new_tables = await conn.run_sync(
            lambda sync_conn: sync_conn.dialect.get_table_names(sync_conn)
        )
        created = set(new_tables) - set(existing)
        if created:
            logger.info(f"  新建數據表: {', '.join(created)}")
        else:
            logger.info("  所有表已存在，無需變更（數據完整保留）")
