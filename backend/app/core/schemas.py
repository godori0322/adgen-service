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
