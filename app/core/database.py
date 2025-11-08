from config import settings
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

DATABASE_URL = settings.database_url

# 연결 풀 설정으로 MySQL 연결 끊김 문제 해결
engine = create_async_engine(
    DATABASE_URL,
    echo=settings.debug,  # debug 모드에서만 SQL 로그 출력
    pool_size=5,  # 기본 연결 풀 크기
    max_overflow=10,  # 추가 연결 허용 수
    pool_recycle=3600,  # 1시간마다 연결 재생성 (MySQL wait_timeout보다 짧게)
    pool_pre_ping=True,  # 연결 사용 전 상태 확인 (끊어진 연결 자동 재연결)
    pool_reset_on_return='commit',  # 연결 반환 시 커밋으로 리셋
)

AsyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()



