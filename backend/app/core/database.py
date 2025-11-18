# database.py
# SQLAlchemy 데이터베이스 설정

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# PostgreSQL 연결 (기본값: docker-compose 설정)
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://adgen_user:adgen_password@localhost:5432/adgen_db"
)

# SQLite 폴백 (개발 환경)
if os.getenv("USE_SQLITE") == "true":
    DATABASE_URL = "sqlite:///./adgen.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    pool_pre_ping=True,  # 연결 상태 확인
    pool_size=10,
    max_overflow=20
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """데이터베이스 세션 의존성"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
