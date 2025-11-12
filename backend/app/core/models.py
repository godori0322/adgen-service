# models.py
# SQLAlchemy 모델 정의

from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from backend.app.core.database import Base

class User(Base):
    """사용자 및 사업자 정보 모델"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # 사업자 정보
    business_type = Column(String(50), nullable=True)  # 업종 (ex: 카페, 음식점, 미용실)
    location = Column(String(100), nullable=True)  # 가게 위치
    menu_items = Column(Text, nullable=True)  # 메뉴 (JSON string)
    business_hours = Column(String(100), nullable=True)  # 영업시간
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
