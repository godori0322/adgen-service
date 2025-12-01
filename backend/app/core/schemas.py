# schemas.py
# backend/app/core/schemas.py

# ChatMessage, DialogueRequests, DialogueResponse 통합(multi-turn)

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Any, Literal
from enum import Enum

# ==================== 공통 Base 응답 ====================

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
                "timestamp": "2025-11-11T09:00:00Z",
            }
        }


# ==================== Whisper / GPT ====================

class WhisperResponse(BaseResponse):
    text: str = Field(..., description="Whisper 모델로 변환된 텍스트")


class GPTRequest(BaseModel):
    text: str = Field(..., description="사용자의 요청(ex: 오늘 손님이 줄었는데...)")
    context: Optional[str] = Field(None, description="날씨, 업종, 행사 등 부가정보")

     # 생성 옵션 플래그
    generate_image: bool = Field(
        default=True,
        description="이미지 생성 여부 (기본값: True)",
    )
    generate_audio: bool = Field(
        default=False,
        description="BGM 생성 여부 (기본값: False)",
    )
    generate_video: bool = Field(
        default=False,
        description="이미지+오디오 mp4 합성 여부 (기본값: False, generate_audio=True일 때만 의미)",
    )
   

    class Config:
        json_schema_extra = {
            "example": {
                "text": "이번 주말 브런치 이벤트 홍보해줘",
                "context": "서울, 카페, 주말 한정 브런치 세트",
                "generate_image": True,
                "generate_audio": True,
                "generate_video": True,
            }
        }


class GPTResponse(BaseResponse):
    idea: str = Field(..., description="추천 이벤트/마케팅 아이디어")
    caption: str = Field(..., description="홍보용 문구")
    hashtags: List[str] = Field(..., description="자동 생성된 해시태그 목록")
    image_prompt: str = Field(..., description="이미지 생성용 프롬프트")
    bgm_prompt: Optional[str] = Field(
        default=None,
        description="Stable Audio용 BGM 프롬프트(장르/무드/템포 등 영어 설명)",
    )    


class AdGenerateResponse(GPTResponse):
    idea: str
    caption: str
    hashtags: List[str]
    image_prompt: str

    image_base64: Optional[str] = Field(
        None,
        description="base64 인코딩된 PNG 이미지 데이터(접두사 없이, 내부 미리보기용)")
    image_url: Optional[str] = Field(
        None,
        description="생성된 이미지를 직접 다운로드/공유할 수 있는 절대 URL",
    )
    audio_url: Optional[str] = Field(
        None,
        description="생성된 BGM을 다운로드/공유할 수 있는 절대 URL",
    )
    video_url: Optional[str] = Field(
        None,
        description="이미지와 BGM을 합성한 mp4 광고 영상의 절대 URL",
    )


# ==================== Audio Geneartion (Stable Audio Open) ====================
class AudioGenerationRequest(BaseModel):
    """
    Stable Audio Open을 통한 BGM 생성을 위한 요청 스키마 정의.
    지금은 최소한으로 prompt + duration_sec만 받는 구조.
    """
    prompt: str = Field(
        ...,
        description="배경음악에 대한 자연어 설명 (예: 따뜻한 재즈 느낌으로 20초짜리 GBM)",
    )
    duration_sec: float = Field(
        20.0,
        ge=1.0,
        le=30.0,
        description="음악 길이(초). musicgen 최대 약 47초. PoC는 15초 제한",
    )

class AudioGenerationResponse(BaseResponse):
    """
    BGM 생성 결과 응답 스키마 정의.
    BaseResponse를 상속해서 status/message/timestamp를 함께 반환.
    """
    audio_url: str = Field(..., description="생성된 오디오를 재생할 수 있는 URL 경로")
    # 예: /media/audio/3f2a9c4b0e4d4c8f8a12d9f3ab8d90a1.wav

    prompt: str = Field(..., description="모델에 전달된 최종 프롬프트 문자열")
    # 나중에 프리셋/영문 설명을 합치면, 실제 사용된 full prompt를 넣을 수 있음

    duration_sec: float = Field(..., description="생성 요청에 사용된 길이(초)")






# ==================== Diffusion 관련 스키마 ====================

# 의도 라벨링 스키마
class CompositionMode(str, Enum):
    rigid = "rigid"
    balanced = "balanced"
    creative = "creative"


# 단순 이미지 생성 요청(필요 시 사용)
class DiffusionRequest(BaseModel):
    prompt: str = Field(..., description="이미지 생성용 프롬프트")


# 1) 누끼/마스크를 클라이언트가 직접 주는 고급 API
#    → 프리셋 기반 + override (개발자 UX 통일)
class DiffusionControlRequest(BaseModel):
    # 텍스트 정보
    prompt: str = Field(..., description="생성할 배경에 대한 텍스트 프롬프트")

    # 이미지 정보
    original_image_b64: str = Field(
        ...,
        description="원본 제품 이미지 (Base64). Depth Map과 IP-Adapter 임베딩 추출에 사용.",
    )
    mask_b64: str = Field(
        ...,
        description="누끼팀(MobileSAM)이 추출한 흑백 마스크 (Base64). Inpainting/합성 영역 지정에 사용.",
    )

    # 제어 강도 파라미터(프리셋 + override)
    control_weight: float | None = Field(
        default=None,
        description=(
            "ControlNet (Depth) 제어 강도. "
            "None이면 내부 프리셋 기본값(예: balanced 프리셋 값) 사용."
        ),
    )
    ip_adapter_scale: float | None = Field(
        default=None,
        description=(
            "IP-Adapter 스타일 강도. "
            "None이면 내부 프리셋 기본값(예: balanced 프리셋 값) 사용."
        ),
    )


# 2) Auto API: 원본 제품 이미지만 주면
#    - 내부에서 MobileSAM + SAM으로 누끼/마스크 추출
#    - CompositionMode 프리셋 + override
class DiffusionAutoRequest(BaseModel):
    prompt: Optional[str] = Field(
        "A cinematic, studio-lit product hero shot on a clean background",
        description="배경/분위기에 대한 텍스트 프롬프트 (미입력 시 기본값 사용)",
    )
    product_image_b64: str = Field(
        ...,
        description="사용자가 업로드한 원본 제품 이미지(Base64)",
    )
    composition_mode: CompositionMode = Field(
        default=CompositionMode.balanced,
        description="합성 모드 (rigid/balanced/creative)",
    )
    # 프리셋 값 덮어쓰기용 (None이면 프리셋 그대로 사용)
    control_weight: float | None = Field(
        default=None,
        description="프리셋 ControlNet 값을 덮어쓰고 싶은 경우에만 사용. None이면 프리셋 값 사용.",
    )
    ip_adapter_scale: float | None = Field(
        default=None,
        description="프리셋 IP-Adapter 값을 덮어쓰고 싶은 경우에만 사용. None이면 프리셋 값 사용.",
    )


# 최종 이미지 반환
class DiffusionControlResponse(BaseModel):
    image_b64: str = Field(..., description="배경 합성 및 Control이 완료된 최종 이미지 (Base64)")


class DiffusionResponse(BaseResponse):
    image_url: Optional[str] = Field(None, description="생성된 이미지 URL")



# ==================== Meida Generation====================
class AdMediaGenerateRequest(BaseModel):
    text: str = Field(..., description="사용자가 최종적으로 요청한 문장")
    context: Optional[str] = Field(
        default=None,
        description="GPT 멀티턴 결과로 정리된 전략/맥락 요약 문자열",
    )

    idea: Optional[str] = Field(
        default=None,
        description="GPT가 생성한 광고 아이디어 문장",
    )
    caption: Optional[str] = Field(
        default=None,
        description="SNS/포스터에 들어갈 메인 카피 문장",
    )
    hashtags: List[str] = Field(
        default_factory=list,
        description="광고 해시태그 리스트",
    )

    image_prompt: Optional[str] = Field(
        default=None,
        description="이미지 생성용 프롬프트 (GPT가 만든 것)",
    )
    bgm_prompt: Optional[str] = Field(
        default=None,
        description="BGM 생성용 프롬프트 (GPT가 만든 것)",
    )

    # 🔹 제품 이미지(Base64) 필수
    product_image_b64: str = Field(
        ...,
        description="사용자가 업로드한 제품 이미지(Base64 문자열)",
    )

    # 🔹 합성 모드
    composition_mode: CompositionMode = Field(
        default=CompositionMode.balanced,
        description="제품+배경 합성 모드 (rigid | balanced | creative)",
    )

    generate_image: bool = Field(
        default=True,
        description="이미지 생성 여부 플래그",
    )
    generate_audio: bool = Field(
        default=False,
        description="BGM 생성 여부 플래그",
    )
    generate_video: bool = Field(
        default=False,
        description="이미지 + 오디오 mp4 합성 여부 플래그",
    )



# ==================== Weather / History ====================

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


# ==================== Multi-turn Dialogue ====================

# langchain이 출력할 최종 콘텐츠의 pydantic 스키마
class FinalContentSchema(BaseModel):
    idea: str = Field(..., description="추천 이벤트/마케팅 아이디어")
    caption: str = Field(..., description="홍보용 문구")
    hashtags: List[str] = Field(..., description="자동 생성된 해시태그 목록")
    image_prompt: str = Field(..., description="이미지 생성용 프롬프트")
    bgm_prompt: Optional[str] = Field(
        default=None,
        description="MusicGen용 BGM 분위기/스타일 프롬프트",
    )

    # 이미지/이미지+오디오/비디오 선택 옵션 추가
    generate_mode: Optional[str] = Field(
        default="image_only",
        description="사용자가 선택한 생성 모드(image_only | image_audio | image_audio_vide)"
    )

# GPT 내부 응답(대화 상태 - 기본형)
class DialogueGPTResponse(BaseModel):
    is_complete: bool = Field(..., description="정보 수집 완료 여부. True면 대화 종료.")
    next_question: Optional[str] = Field(None, description="다음으로 사용자에게 물어볼 질문 텍스트")
    final_content: Optional[FinalContentSchema] = Field(
        None, description="수집 완료 후 GPT가 생성한 최종 콘텐츠"
    )


# 광고 생성용 GPT 응답 스키마
class DialogueGPTResponse_AD(BaseModel):
    type: Literal["ad"] = Field(default="ad", description="응답 타입 (고정값: ad)")
    is_complete: bool = Field(..., description="정보 수집 완료 여부. True면 대화 종료.")
    next_question: Optional[str] = Field(None, description="다음으로 사용자에게 물어볼 질문 텍스트")
    final_content: Optional[FinalContentSchema] = Field(
        None, description="수집 완료 후 GPT가 생성한 최종 콘텐츠"
    )
    conversation_history: Optional[List[dict]] = Field(
        None,
        description="대화 완료 시 전체 대화 기록 (메모리 업데이트용)",
    )
    session_key: Optional[str] = Field(
        None,
        description="세션 키 (user-{id} 또는 guest-{uuid})",
    )


# 프로필/정보 업데이트용 GPT 응답 스키마
class DialogueGPTResponse_Profile(BaseModel):
    type: Literal["profile"] = Field(default="profile", description="응답 타입 (고정값: profile)")
    is_complete: bool = Field(..., description="정보 수집 완료 여부. True면 대화 종료.")
    next_question: Optional[str] = Field(None, description="다음으로 사용자에게 물어볼 질문 텍스트")
    last_ment: Optional[str] = Field(
        None,
        description="PROFILE_BUILDING/INFO_UPDATE 완료 시 표시할 확인 메시지",
    )
    conversation_history: Optional[List[dict]] = Field(
        None,
        description="대화 완료 시 전체 대화 기록 (메모리 업데이트용)",
    )
    session_key: Optional[str] = Field(
        None,
        description="세션 키 (user-{id} 또는 guest-{uuid})",
    )


# 클라이언트에게 나가는 응답
class DialogueResponse(BaseResponse):
    is_complete: bool = Field(..., description="정보 수집 완료 여부.")
    user_text: str = Field(..., description="이번 턴에 사용자가 말한 내용")
    next_question: Optional[str] = Field(None, description="다음 질문 텍스트")
    final_content: Optional[FinalContentSchema] = Field(None, description="최종 콘텐츠")
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
                "business_hours": "09:00-22:00",
            }
        }

class UserNameFind(BaseModel):
    """사용자 아이디 찾기 요청"""
    email: str = Field(..., description="이메일")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "owner@example.com",
            }
        }

class PasswordFind(BaseModel):
    """사용자 비밀번호 찾기 요청"""
    username: str = Field(..., min_length=3, max_length=50, description="사용자 아이디")
    email: str = Field(..., description="이메일")

    class Config:
        json_schema_extra = {
            "example": {
                "username": "cafe_owner",
                "email": "owner@example.com",
            }
        }

class PasswordReset(BaseModel):
    """사용자 비밀번호 리셋 요청"""
    username: str = Field(..., min_length=3, max_length=50, description="사용자 아이디")
    password: str = Field(..., min_length=6, description="비밀번호")

    class Config:
        json_schema_extra = {
            "example": {
                "username": "cafe_owner",
                "password": "securepass123",
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


# ==================== 광고 요청 기록 ====================

class AdRequestResponse(BaseModel):
    """광고 요청 처리 정보 응답"""
    id: int
    user_id: Optional[int]
    voice_text: Optional[str]
    weather_info: Optional[str]
    gpt_output_text: Optional[str]
    diffusion_prompt: Optional[str]
    image_url: Optional[str]
    audio_url: Optional[str]      # 추가 --> 히스토리/마이페이지에서 BGM/mp4 사용가능하도록
    video_url: Optional[str]      # 추가 --> 히스토리/마이페이지에서 BGM/mp4 사용가능하도록
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
            "characteristics": ["조용한 공간 선호"],
        },
    )

    competitive_advantage: Optional[List[str]] = Field(
        default=None,
        description="차별화 포인트",
        example=["넓은 공간", "조용한 분위기"],
    )

    brand_concept: Optional[dict] = Field(
        default=None,
        description="브랜드 컨셉",
        example={
            "keywords": ["북유럽 감성", "힐링"],
            "tone": "차분하고 따뜻한",
        },
    )

    marketing_goals: Optional[List[str]] = Field(
        default=None,
        description="마케팅 목표",
        example=["평일 오후 매출 증대", "신규 고객 유치"],
    )

    preferences: Optional[dict] = Field(
        default=None,
        description="마케팅 선호도",
        example={
            "channels": ["인스타그램"],
            "content_style": ["감성 사진"],
        },
    )


# ==================== History ====================

class AdHistoryItem(BaseModel):
    """광고 히스토리 개별 항목"""
    id: int = Field(..., description="광고 요청 ID")
    created_at: datetime = Field(..., description="생성 날짜 및 시간")
    idea: Optional[str] = Field(None, description="광고 아이디어")
    caption: Optional[str] = Field(None, description="캡션")
    hashtags: Optional[str] = Field(None, description="해시태그 문자열")
    image_url: Optional[str] = Field(None, description="이미지 URL")
    audio_url: Optional[str] = Field(None, description="오디오 URL")
    video_url: Optional[str] = Field(None, description="비디오 URL")

    class Config:
        from_attributes = True


class AdHistoryResponse(BaseModel):
    """광고 히스토리 응답"""
    total: int = Field(..., description="전체 히스토리 개수")
    history: List[AdHistoryItem] = Field(..., description="히스토리 항목 리스트")

    class Config:
        from_attributes = True
