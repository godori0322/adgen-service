# schemas.py
# ChatMessage, DialogueRequests, DialogueResponse 통합(multi-turn)

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Any, Literal
from enum import Enum

# 기본 응답구조
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

# 기존 서비스 스키마
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

# 의도 라벨링 스키마 추가
class CompositionMode(str, Enum):
    rigid = "rigid"
    balanced = "balanced"
    creative = "creative"

# 이미지 생성 관련 스키마 그룹
class DiffusionRequest(BaseModel):
    prompt: str = Field(..., description="이미지 생성용 프롬프트")
# DiffusionRequest는 multipart/form-data로 받으므로 스키마 불필요
# 실제 엔드포인트에서는 Form()과 File()을 사용합니다.

# =============ControlNet/IP-Adapter 요청 스키마(추가)===========================
class DiffusionControlRequest(BaseModel):
    # 텍스트 정보
    prompt: str = Field(..., description="생성할 배경에 대한 텍스트 프롬프트")
    # 이미지 정보(누끼 처리된 제품 사진) -> 누끼딴 이미지의 base64 문자열
    original_image_b64: str = Field(..., description="원본 제품 이미지 (Base64). Depth Map과 IP-Adapter 임베딩 추출에 사용.")
    mask_b64: str = Field(..., description="누끼팀(MobileSAM)이 추출한 흑백 마스크 (Base64). Inpainting 영역 지정에 사용.")   
    # 제어 강도 파라미터(튜닝용)
    # Controlnet Depth 강도
    control_weight: Optional[float] = Field(1.0, ge=0.0, le=2.0, description="ControlNet (Depth) 제어 강도. 1.0 권장.")
    # IP-Adapter 강도 (스타일 주입)
    ip_adapter_scale: Optional[float] = Field(0.7, ge=0.0, le=1.0, description="IP-Adapter 스타일 주입 강도. 0.7 권장.")

# 누끼 추출부터 배경 합성까지 한 번에 처리하는 요청 스키마
# 의도 라벨링 추가
class DiffusionAutoRequest(BaseModel):
    prompt: Optional[str] = Field(
        "A cinematic, studio-lit product hero shot on a clean background",
        description="배경/분위기에 대한 텍스트 프롬프트 (미입력 시 기본값 사용)",
    )
    product_image_b64: str = Field(
        ...,
        description="사용자가 업로드한 원본 제품 이미지(Base64)")
    composition_mode: CompositionMode = Field(
        default=CompositionMode.balanced,
        description="합성 모드 (rigid/balanced/creative)"
    )
    control_weight: float | None = Field(
        default=None,
        description="프리셋을 덮어쓰고 싶은 경우에만 사용. 기본은 프리셋 값"
    )
    ip_adapter_scale: float | None = Field(
        default=None,
        description="프리셋을 덮어쓰고 싶은 경우에만 사용. 기본은 프리셋 값"
    )
    # control_weight: Optional[float] = Field(
    #     0.7, ge=0.0, le=2.0, description="ControlNet (Depth) 제어 강도. 0.5~0.9 권장."
    # )
    # ip_adapter_scale: Optional[float] = Field(
    #     0.1, ge=0.0, le=1.0, description="IP-Adapter 스타일 주입 강도. 0.1~0.3 권장."
    # )

# 최종 이미지 반환
class DiffusionControlResponse(BaseModel):
    image_b64: str = Field(..., description="배경 합성 및 Control이 완료된 최종 이미지 (Base64)")


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


# ============== Multi-turn Dialogue 스키마(추가) ==============
# lanchain이 출력할 최종 콘텐츠의 pydantic 스키마
class FinalContentSchema(BaseModel):
    idea: str = Field(..., description="추천 이벤트/마케팅 아이디어")
    caption: str = Field(..., description="홍보용 문구")
    hashtags: List[str] = Field(..., description="자동 생성된 해시태그 목록")
    image_prompt: str = Field(..., description="이미지 생성용 프롬프트")

# 광고 생성용 GPT 응답 스키마
class DialogueGPTResponse_AD(BaseModel):
    type: Literal["ad"] = Field(default="ad", description="응답 타입 (고정값: ad)")
    is_complete: bool = Field(..., description="정보 수집 완료 여부. True면 대화 종료.")
    next_question: Optional[str] = Field(None, description="다음으로 사용자에게 물어볼 질문 텍스트")
    final_content: Optional[FinalContentSchema] = Field(None, description="수집 완료 후 GPT가 생성한 최종 콘텐츠")
    conversation_history: Optional[List[dict]] = Field(None, description="대화 완료 시 전체 대화 기록 (메모리 업데이트용)")
    session_key: Optional[str] = Field(None, description="세션 키 (user-{id} 또는 guest-{uuid})")

# 프로필/정보 업데이트용 GPT 응답 스키마
class DialogueGPTResponse_Profile(BaseModel):
    type: Literal["profile"] = Field(default="profile", description="응답 타입 (고정값: profile)")
    is_complete: bool = Field(..., description="정보 수집 완료 여부. True면 대화 종료.")
    next_question: Optional[str] = Field(None, description="다음으로 사용자에게 물어볼 질문 텍스트")
    last_ment: Optional[str] = Field(None, description="PROFILE_BUILDING/INFO_UPDATE 완료 시 표시할 확인 메시지")
    conversation_history: Optional[List[dict]] = Field(None, description="대화 완료 시 전체 대화 기록 (메모리 업데이트용)")
    session_key: Optional[str] = Field(None, description="세션 키 (user-{id} 또는 guest-{uuid})")

# 클라이언트에게 전달될 최종 응답 스키마 (dialog.py 에서 사용)
class DialogueResponse(BaseResponse):
    is_complete: bool = Field(..., description="정보 수집 완료 여부.")
    user_text: str = Field(..., description="이번 턴에 사용자가 말한 내용")
    next_question: Optional[str] = Field(None, description="다음 질문 텍스트")
    final_content: Optional[FinalContentSchema] = Field(None, description= "최종 콘텐츠")
    session_id: str = Field(..., description="현재 대화 세션을 식별하는 ID")

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

# ==================== 마케팅 전략 정보 스키마 ====================

class MarketingStrategy(BaseModel):
    """마케팅 전략 정보 (JSON 저장용)"""
    
    target_audience: Optional[dict] = Field(
        default=None,
        description="타겟 고객 정보",
        example={
            "age_group": ["20대", "30대"],
            "occupation": ["직장인"],
            "gender": "여성",
            "characteristics": ["조용한 공간 선호"]
        }
    )
    
    competitive_advantage: Optional[List[str]] = Field(
        default=None,
        description="차별화 포인트",
        example=["넓은 공간", "조용한 분위기"]
    )
    
    brand_concept: Optional[dict] = Field(
        default=None,
        description="브랜드 컨셉",
        example={
            "keywords": ["북유럽 감성", "힐링"],
            "tone": "차분하고 따뜻한"
        }
    )
    
    marketing_goals: Optional[List[str]] = Field(
        default=None,
        description="마케팅 목표",
        example=["평일 오후 매출 증대", "신규 고객 유치"]
    )
    
    preferences: Optional[dict] = Field(
        default=None,
        description="마케팅 선호도",
        example={
            "channels": ["인스타그램"],
            "content_style": ["감성 사진"]
        }
    )
