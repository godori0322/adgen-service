# init_db.py
# 데이터베이스 초기화 스크립트

from backend.app.core.database import engine, Base
from backend.app.core.models import User

def init_db():
    """데이터베이스 테이블 생성"""
    print("데이터베이스 테이블 생성 중...")
    Base.metadata.create_all(bind=engine)
    print("✅ 데이터베이스 초기화 완료!")

if __name__ == "__main__":
    init_db()
