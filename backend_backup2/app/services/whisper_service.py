# # ==========================================================================
# # backend/app/services/whisper_service.py

# # backend/app/services/whisper_service.py

# import torch
# import io
# import os
# import soundfile as sf
# from fastapi import UploadFile, HTTPException
# import numpy as np
# from transformers import AutoProcessor
# from transformers.models.auto.modeling_auto import AutoModelForSpeechSeq2seq

# # --- 1. 모델 초기 로드 (서버 시작 시 1회 실행) ---
# # 파인튜닝할 베이스 모델: large-v3 권장
# MODEL_ID = "openai/whisper-small" 

# # GPU 사용 가능 여부 확인 및 설정
# device = "cuda:0" if torch.cuda.is_available() else "cpu"
# # GPU 사용 시 메모리 효율을 위해 float16, CPU 사용 시 float32
# torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

# # 모델과 프로세서를 Hugging Face Hub에서 로드
# try:
#     print(f"Loading Whisper Model '{MODEL_ID}' on {device}...")
#     processor = AutoProcessor.from_pretrained(MODEL_ID)
#     model = AutoModelForSpeechSeq2seq.from_pretrained(
#         MODEL_ID, 
#         torch_dtype=torch_dtype, 
#         low_cpu_mem_usage=True, 
#         use_safetensors=True
#     ).to(device)
#     print(f"Whisper Model '{MODEL_ID}' loaded successfully on {device}!")

# except Exception as e:
#     # 모델 로드 실패 시 서버 시작을 막습니다. (인터넷 연결 또는 GPU 메모리 문제)
#     print(f"ERROR: Failed to load Whisper model: {e}")
#     # HTTPException 대신 RuntimeError를 사용하여 서버 시작 시 오류를 명확히 함
#     raise RuntimeError(f"Whisper 모델 로드 실패: {e}") 
    

# def transcribe_audio(file: UploadFile) -> str:
#     # 모델 로드 성공 시에만 이 함수가 호출됩니다.
    
#     # 1. UploadFile에서 오디오 바이트 추출
#     try:
#         file_content = file.file.read()
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"파일 읽기 오류: {e}")

#     if not file_content:
#         raise HTTPException(status_code=400, detail="업로드된 오디오 파일 내용이 비어 있습니다.")

#     # 2. 오디오 바이트를 NumPy 배열로 변환
#     try:
#         # io.BytesIO를 사용하여 메모리에서 soundfile로 데이터를 전달
#         audio_data, sampling_rate = sf.read(io.BytesIO(file_content), dtype='float32')
        
#         # Whisper 모델은 16kHz를 기대합니다. 샘플링 레이트 불일치 시 경고 또는 리샘플링 필요
#         if sampling_rate != 16000:
#              # 실제 프로덕션에서는 리샘플링 로직이 필요하지만, 현재는 16kHz 전송을 전제로 합니다.
#              print(f"Warning: Expected 16kHz, but got {sampling_rate}Hz. Accuracy may be affected.") 

#     except Exception as e:
#         # soundfile이 파일을 읽지 못하는 경우 (손상되거나 비표준 포맷)
#         raise HTTPException(status_code=415, detail=f"오디오 파일 처리 실패: 유효한 16kHz WAV 파일인지 확인하세요. (오류: {e})")

#     # 3. 모델 입력 형태로 변환 및 장치(Device)로 이동
#     input_features = processor(
#         audio_data, 
#         sampling_rate=sampling_rate, 
#         return_tensors="pt"
#     ).input_features.to(device)
    
#     # 4. 모델 전사(추론) 실행
#     # 한국어 전용으로 설정
#     predicted_ids = model.generate(
#         input_features,
#         language="ko", 
#         max_length=448 
#     )

#     # 5. ID를 텍스트로 디코딩
#     transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
#     return transcription.strip()  # 양쪽 공백 제거 


# ==========================================================================
# backend/app/services/whisper_service.py
# Hugging Face pipeline을 사용한 large-v3 로컬 모델 연동

import torch
import io
from fastapi import UploadFile, HTTPException
from transformers import pipeline
import os
import soundfile as sf # soundfile로 WAV 파일 읽기
import numpy as np
from scipy.signal import resample_poly # 리샘플링 라이브러리--> 16kHz로 리샘플링 위해 추가

# --- 1. 모델 초기 로드 (서버 시작 시 1회 실행) ---
# 사용자가 지정한 모델 (최고 성능, 최대 자원 요구)
MODEL_ID = "openai/whisper-large-v3" 

# GPU 사용 가능 여부 확인 및 설정
# CUDA 장치가 사용 가능하고, 사용 가능한 장치가 있을 경우에만 GPU 사용
device = "cuda:0" if torch.cuda.is_available() and torch.cuda.device_count() > 0 else "cpu"
# GPU 메모리 절약을 위해 float16 사용 (CPU 사용 시는 float32)
torch_dtype = torch.float16 if device == "cuda:0" else torch.float32


# pipline 로드
try:
    print(f"Loading Whisper Model '{MODEL_ID}' using pipeline on {device}...")
    
    # Hugging Face Pipeline 설정: 로딩과 전처리를 모두 추상화하여 안정성 향상
    whisper_pipeline = pipeline(
        "automatic-speech-recognition",
        model=MODEL_ID,
        device=device, # 모델을 GPU/CPU로 이동
        torch_dtype=torch_dtype,
        # large 모델 로딩 시 accelerate가 자동으로 저메모리 로딩을 시도
    )
    print(f"Whisper Pipeline loaded successfully! Device: {device}")
except Exception as e:
    print(f"FATAL ERROR: Failed to load Whisper model pipeline. Check GPU memory or switch to 'base' model: {e}")
    raise RuntimeError(f"Whisper Pipeline 로드 실패: {e}") 
    
    
def transcribe_audio(file: UploadFile) -> str:
    # 1. 파일 내용 읽기
    try:
        file_content = file.file.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 읽기 오류: {e}")

    if not file_content:
        raise HTTPException(status_code=400, detail="업로드된 오디오 파일 내용이 비어 있습니다.")

    # 2. 오디오 전처리 : numpy 배열 변환, 모노 변환, 리샘플링
    TARGET_SR = 16000   # whisper 모델의 학습 샘플링 레이트

    try:
        # 오디오 배열 & 원래 샘플링 레이트 추출
        audio_io = io.BytesIO(file_content)
        # soundfile.read()를 사용 --> BytesIO에서 numpy 배열과 샘플링 레이트 추출
        audio_array, sampling_rate = sf.read(audio_io, dtype='float32')

        # 채녈 변환 : 스테레오 -> 모노
        if audio_array.ndim > 1:
            # 여러 채녈 평균 내어 모노로 변환
            audio_array = np.mean(audio_array, axis=1)
        
        # 샘플링 레이트 변환 : resampling
        if sampling_rate != TARGET_SR:
            # spicy.signal.resample_poly를 사용하여 고품질 리샘플링 수행
            audio_array = resample_poly(audio_array, TARGET_SR, sampling_rate)
            sampling_rate = TARGET_SR  # 리샘플링 후 샘플링 레이트 업데이트
        
        # 경고 방지 : dtype -> float32로 명시 (파이프라인이 선호함)
        audio_array = audio_array.astype(np.float32)
    
    except Exception as e:
        raise HTTPException(status_code=415, detail = f"오디오 파일 처리 실패 (soundfile): 유효한 오디오 형식인지 확인필요 (오류: {e}")

    # 3. 모델 전사(추론) 실행 및 튜닝 파라미터 적용
    try:
        # numpy 배열(audio_array)을 pipeline에 직접 전달
        result = whisper_pipeline(
            audio_array,
            # 튜닝 파라미터
            generate_kwargs={
                "language": "ko",
                "task": "transcribe",
            #     # 전사 정확도 향상을 위한 프롬프트 -> whisper large 모델이 허용안해서 삭제
            #     "initial_prompt": "타겟 고객 연령, 타겟 고객 특징, 운영하는 가게의 업종, 가게의 분위기, 가게의 위치, 가게의 이름, 상권 특징에 대해서 말해주세요."
            },
        )

        # 4. 결과 반환
        return result['text'].strip()

    except Exception as e:
        # OOM 오류, 오디오 포맷 오류 등 추론 중 발생한 오류
        raise HTTPException(status_code=500, detail=f"Whisper 파이프라인 추론 오류: {e}")