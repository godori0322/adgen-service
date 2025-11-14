# schemas.py

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Any

class BaseResponse(BaseModel):
    status: str = Field(default="success", description="응답 상태")
    message: Optional[str] = Field(default=None, description="추가 설명")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="응답 생성 시각")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "요청이 성공적으로 처리되었습니다.",
                "timestamp": "2025-11-11T09:00:00Z"
            }
        }

class WhisperResponse(BaseResponse):
    text: str = Field(..., description="Whisper 모델로 변환된 텍스트")

class GPTRequest(BaseModel):
    text: str = Field(..., description="사용자의 요청(ex: 오늘 손님이 줄었는데...)")
    context: Optional[str] = Field(None, description="날씨, 업종, 행사 등 부가정보")

    class Config:
        json_schema_extra = {
            "example": {
                "text": "오늘 손님이 너무 없는데 뭐 올리면 좋을까?",
                "context": "서울, 비 오는 날, 일식집"
            }
        }

class GPTResponse(BaseResponse):
    idea: str = Field(..., description="추천 이벤트/마케팅 아이디어")
    caption: str = Field(..., description="홍보용 문구")
    hashtags: List[str] = Field(..., description="자동 생성된 해시태그 목록")
    image_prompt: str = Field(..., description="이미지 생성용 프롬프트")

class AdGenerateResponse(GPTResponse):
    image_base64: str = Field(..., description="base64 인코딩된 PNG 이미지 데이터(접두사 없이)")

class DiffusionRequest(BaseModel):
    prompt: str = Field(..., description="이미지 생성용 프롬프트")

class DiffusionResponse(BaseResponse):
    image_url: Optional[str] = Field(None, description="생성된 이미지 URL")

class WeatherResponse(BaseResponse):
    city: str = Field(..., description="도시 이름")
    temp: float = Field(..., description="현재 기온 (°C)")
    desc: str = Field(..., description="날씨 설명 (맑음, 비, 흐림 등)")

class HistoryItem(BaseModel):
    id: int
    request_text: str
    result_text: str
    created_at: datetime

class HistoryResponse(BaseResponse):
    items: List[HistoryItem]

# ==================== 인증 관련 스키마 ====================

class UserCreate(BaseModel):
    """사용자 회원가입 요청"""
    username: str = Field(..., min_length=3, max_length=50, description="사용자 아이디")
    email: str = Field(..., description="이메일")
    password: str = Field(..., min_length=6, description="비밀번호")
    business_type: Optional[str] = Field(None, description="업종 (ex: 카페, 음식점, 미용실)")
    location: Optional[str] = Field(None, description="가게 위치")
    menu_items: Optional[List[str]] = Field(None, description="메뉴 목록")
    business_hours: Optional[str] = Field(None, description="영업시간")

    class Config:
        json_schema_extra = {
            "example": {
                "username": "cafe_owner",
                "email": "owner@example.com",
                "password": "securepass123",
                "business_type": "카페",
                "location": "서울 강남구",
                "menu_items": ["아메리카노", "라떼", "케이크"],
                "business_hours": "09:00-22:00"
            }
        }

class UserUpdate(BaseModel):
    """사용자 정보 수정"""
    business_type: Optional[str] = None
    location: Optional[str] = None
    menu_items: Optional[List[str]] = None
    business_hours: Optional[str] = None

class UserProfile(BaseModel):
    """사용자 프로필 응답"""
    id: int
    username: str
    email: str
    business_type: Optional[str]
    location: Optional[str]
    menu_items: Optional[str]
    business_hours: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    """JWT 토큰 응답"""
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    """토큰 페이로드 데이터"""
    username: Optional[str] = None

# ==================== 광고 요청 관련 스키마 ====================

class AdRequestResponse(BaseModel):
    """광고 요청 처리 정보 응답"""
    id: int
    user_id: Optional[int]
    voice_text: Optional[str]
    weather_info: Optional[str]
    gpt_output_text: Optional[str]
    diffusion_prompt: Optional[str]
    image_url: Optional[str]
    hashtags: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
