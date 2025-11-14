# models.py
# SQLAlchemy 모델 정의

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
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
    
    # Relationship
    ad_requests = relationship("AdRequest", back_populates="user")


class AdRequest(Base):
    """광고 요청 처리 정보 모델"""
    __tablename__ = "ad_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 비로그인 사용자는 NULL
    
    # 처리 과정 데이터
    voice_text = Column(Text, nullable=True)  # Whisper로 변환된 음성 텍스트
    weather_info = Column(String(200), nullable=True)  # 날씨 정보
    gpt_prompt = Column(Text, nullable=True)  # GPT에 보낸 전체 프롬프트
    gpt_output_text = Column(Text, nullable=True)  # GPT 생성 아이디어 + 캡션
    diffusion_prompt = Column(Text, nullable=True)  # Diffusion 모델에 사용된 프롬프트
    image_url = Column(String(500), nullable=True)  # 생성된 이미지 URL (S3 등)
    hashtags = Column(Text, nullable=True)  # 해시태그 (JSON string)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="ad_requests")
