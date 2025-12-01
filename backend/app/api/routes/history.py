# history.py
# 광고 생성 히스토리 조회 API

from typing import Optional
import json
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.models import User, AdRequest
from backend.app.core.schemas import AdHistoryResponse, AdHistoryItem
from backend.app.services import auth_service

router = APIRouter(prefix="/history", tags=["History"])
security = HTTPBearer(auto_error=False)


def parse_gpt_output(text: Optional[str]) -> dict:
    """
    gpt_output_text를 파싱하여 idea, caption, hashtags 추출
    형식: "아이디어: {idea}\n캡션: {caption}\n해시태그: {hashtags}"
    """
    result = {"idea": None, "caption": None, "hashtags": None}
    
    if not text:
        return result
    
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('아이디어:'):
            result['idea'] = line.split('아이디어:')[1].strip()
        elif line.startswith('캡션:'):
            result['caption'] = line.split('캡션:')[1].strip()
        elif line.startswith('해시태그:'):
            result['hashtags'] = line.split('해시태그:')[1].strip()
    
    return result


@router.get("", response_model=AdHistoryResponse)
async def get_user_history(
    skip: int = 0,
    limit: int = 50,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
):
    """
    로그인한 사용자의 광고 생성 히스토리 조회
    
    - **skip**: 건너뛸 항목 수 (페이지네이션)
    - **limit**: 가져올 최대 항목 수 (기본값: 50)
    
    인증 필수: Bearer 토큰 필요
    """
    # 인증 확인
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="인증이 필요합니다. Authorization 헤더에 Bearer 토큰을 포함해주세요."
        )
    
    token = credentials.credentials
    current_user = auth_service.get_user_from_token(db, token)
    
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="유효하지 않은 토큰입니다."
        )
    
    # 사용자의 광고 요청 히스토리 조회 (삭제되지 않은 것만, 최신순)
    total_count = (
        db.query(AdRequest)
        .filter(
            AdRequest.user_id == current_user.id,
            AdRequest.is_deleted == False
        )
        .count()
    )
    
    ad_requests = (
        db.query(AdRequest)
        .filter(
            AdRequest.user_id == current_user.id,
            AdRequest.is_deleted == False
        )
        .order_by(AdRequest.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    # 히스토리 항목 변환
    history_items = []
    for ad in ad_requests:
        # gpt_output_text 파싱
        parsed = parse_gpt_output(ad.gpt_output_text)
        
        history_items.append(
            AdHistoryItem(
                id=ad.id,
                created_at=ad.created_at,
                idea=parsed['idea'],
                caption=parsed['caption'],
                hashtags=parsed['hashtags'],
                image_url=ad.image_url,
                audio_url=ad.audio_url,
                video_url=ad.video_url,
            )
        )
    
    return AdHistoryResponse(
        total=total_count,
        history=history_items,
    )
