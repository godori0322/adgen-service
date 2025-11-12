# 팀원 설치 가이드

## 🚀 빠른 설치 (5분)

### 1단계: 저장소 클론
```bash
git clone https://github.com/godori0322/adgen-service.git
cd adgen-service/adgen-service
```

### 2단계: 가상환경 설정
```bash
# Python 3.10 이상 확인
python --version

# 가상환경 생성
python -m venv venv

# 가상환경 활성화
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
```

### 3단계: 패키지 설치

**방법 1: pyproject.toml 사용 (추천)**
```bash
pip install -e .
```

**방법 2: requirements.txt 사용 (가볍게)**
```bash
pip install -r requirements.txt
```

**방법 3: 수동 설치 (최소)**
```bash
pip install fastapi uvicorn sqlalchemy passlib python-jose bcrypt python-dotenv openai requests python-multipart
```

### 4단계: 환경변수 설정
```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집 (API 키 입력)
nano .env  # 또는 vi, vim, code 등
```

필수 API 키:
- `OPENAI_API_KEY`: https://platform.openai.com/api-keys
- `HF_API_KEY`: https://huggingface.co/settings/tokens
- `WEATHER_API_KEY`: https://openweathermap.org/api

### 5단계: 서버 실행
```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

접속: http://localhost:8000/docs

---

## ✅ 설치 확인

### 테스트 1: 서버 확인
```bash
curl http://localhost:8000
```
**기대 응답:**
```json
{
  "message": "Voice2Marketing API is running 🚀",
  "version": "1.0.0",
  "docs": "/docs"
}
```

### 테스트 2: 회원가입
```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "test1234",
    "business_type": "카페",
    "location": "서울 강남구",
    "menu_items": ["커피"]
  }'
```

### 테스트 3: 로그인
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=test1234"
```

---

## 🔧 문제 해결

### 문제: `ModuleNotFoundError: No module named 'xxx'`
**해결:**
```bash
pip install -e .
# 또는
pip install 모듈명
```

### 문제: `database locked` 에러
**해결:**
```bash
# 기존 DB 삭제 후 재생성
rm adgen.db
python backend/init_db.py
```

### 문제: 포트 8000 이미 사용 중
**해결:**
```bash
# 다른 포트 사용
uvicorn backend.app.main:app --reload --port 8001

# 또는 기존 프로세스 종료
lsof -ti:8000 | xargs kill -9  # Mac/Linux
```

### 문제: API 키 에러
**해결:**
- `.env` 파일이 올바른 위치에 있는지 확인
- API 키에 따옴표 없이 입력했는지 확인
- `.env` 파일 예시:
  ```
  OPENAI_API_KEY=sk-proj-xxxxx
  HF_API_KEY=hf_xxxxx
  WEATHER_API_KEY=xxxxx
  ```

---

## 📋 선택 사항

### 개발 도구 설치
```bash
pip install -e ".[dev]"  # pytest, black, ruff 포함
```

### AI/ML 전체 기능 (용량 큼)
```bash
pip install torch torchvision torchaudio langchain
```

### Jupyter Notebook
```bash
pip install jupyter ipykernel
jupyter notebook
```

---

## 🌐 배포 (프로덕션)

```bash
# 1. Gunicorn 설치
pip install gunicorn

# 2. 서버 실행
gunicorn backend.app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# 3. 환경변수 확인
# SECRET_KEY를 반드시 변경하세요!
```

---

## 📞 도움 요청

문제가 해결되지 않으면:
1. GitHub Issues에 문의
2. 팀 Slack 채널
3. 에러 로그와 함께 문의

**서버 로그 확인:**
```bash
# 서버 실행 터미널에서 에러 확인
# 또는
tail -f server.log  # 로그 파일이 있는 경우
```
