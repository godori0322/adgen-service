import base64
import sys
import os

def encode_to_base64(filepath):
    """지정된 파일 경로의 이미지를 Base64 문자열로 인코딩합니다."""
    try:
        if not os.path.exists(filepath):
            print(f"[ERROR] 파일을 찾을 수 없습니다: {filepath}")
            return None

        with open(filepath, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            return encoded_string
    except Exception as e:
        print(f"[ERROR] 파일 인코딩 중 오류 발생: {e}")
        return None

if __name__ == "__main__":
    # --- 1. 변환할 원본 이미지 파일 이름을 여기에 정확히 입력하세요 ---
    original_file = "backend/app/services/7cd1bd8d8a00c4b5d7aae6ab45f2a712.jpg" 
    # --- 2. 변환할 마스크 이미지 파일 이름을 여기에 정확히 입력하세요 ---
    mask_file = "backend/app/services/7cd1bd8d8a00c4b5d7aae6ab45f2a712-removebg-preview.png" 

    print("--- Base64 변환 결과 ---")

    # 원본 이미지 Base64 생성
    original_b64 = encode_to_base64(original_file)
    if original_b64:
        # 이 문자열을 original_image_b64 필드에 복사하세요.
        print(f"\n[ORIGINAL_IMAGE_B64] (길이: {len(original_b64)}):")
        print(original_b64)

    # 마스크 이미지 Base64 생성
    mask_b64 = encode_to_base64(mask_file)
    if mask_b64:
        # 이 문자열을 mask_b64 필드에 복사하세요.
        print(f"\n[MASK_B64] (길이: {len(mask_b64)}):")
        print(mask_b64)

    print("\n--- 복사/붙여넣기 후 다시 테스트하세요 ---")