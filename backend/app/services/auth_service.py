# auth_service.py
# 인증 관련 비즈니스 로직 (JWT, 비밀번호 해싱 등)

import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from backend.app.core.models import User
from backend.app.core.schemas import UserCreate, TokenData
import json

# 비밀번호 해싱 설정 (Argon2 사용 - 72바이트 제한 없음, 더 안전)
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# JWT 설정
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7일

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """비밀번호 해싱"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """JWT 액세스 토큰 생성"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[TokenData]:
    """JWT 토큰 디코딩"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return TokenData(username=username)
    except JWTError:
        return None

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """사용자명으로 사용자 조회"""
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """이메일로 사용자 조회"""
    return db.query(User).filter(User.email == email).first()

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """사용자 인증"""
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def create_user(db: Session, user_data: UserCreate) -> User:
    """새 사용자 생성"""
    # 메뉴 리스트를 JSON 문자열로 변환
    menu_items_str = json.dumps(user_data.menu_items, ensure_ascii=False) if user_data.menu_items else None
    
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        business_type=user_data.business_type,
        location=user_data.location,
        menu_items=menu_items_str,
        business_hours=user_data.business_hours
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user_profile(db: Session, user_id: int, update_data: dict) -> User:
    """사용자 프로필 업데이트"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    
    # 메뉴 리스트가 있으면 JSON 문자열로 변환
    if "menu_items" in update_data and update_data["menu_items"]:
        update_data["menu_items"] = json.dumps(update_data["menu_items"], ensure_ascii=False)
    
    for key, value in update_data.items():
        if value is not None and hasattr(user, key):
            setattr(user, key, value)
    
    db.commit()
    db.refresh(user)
    return user
