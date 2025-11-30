# media_service.py
# backend/app/service/media_service.py

from pathlib import Path
from uuid import uuid4

from moviepy import AudioFileClip, ImageClip, VideoFileClip  # moviepy 필요


# media 루트 디렉토리 ---> DB 기능 / shared directory로 변경 필요
MEDIA_ROOT = Path("media")
IMAGE_DIR = MEDIA_ROOT / "images"
VIDEO_DIR = MEDIA_ROOT / "video"


def save_generated_image(image_bytes: bytes, ext: str = "png") -> Path:
    """
    Diffusion으로 생성된 이미지를 media/images 아래에 저장하고
    파일 경로(Path)를 반환하는 함수.
    """
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid4().hex}.{ext}"
    file_path = IMAGE_DIR / filename

    with open(file_path, "wb") as f:
        f.write(image_bytes)

    return file_path


def compose_image_and_audio_to_mp4(
    image_path: Path,
    audio_path: Path,
    fps: int = 24,
) -> Path:
    """
    정지 이미지 + 오디오를 이용해 mp4 영상 생성 함수

    image_path: PNG 등 정지 이미지 파일 경로
    audio_path: wav 등 오디오 파일 경로
    return: 생성된 mp4 파일의 Path 객체
    """

    # 1) 오디오 클립 로드
    audio_clip = AudioFileClip(str(audio_path))

    # 2) 이미지 클립 생성
    #    - moviepy 2.x에서는 set_duration이 사라지고 with_duration / duration 인자가 사용됨
    #    - 여기서는 생성자에서 duration을 직접 지정하는 방식 사용
    image_clip = ImageClip(
        str(image_path),
        duration=audio_clip.duration,  # 영상 길이를 오디오 길이와 동일하게 설정
    )

    # 3) 이미지 클립에 오디오 붙이기
    #    - set_audio -> with_audio 로 변경 (v2 스타일)
    video_clip = image_clip.with_audio(audio_clip)

    # 4) 출력 디렉터리 및 파일 경로 설정
    output_dir = Path("media/video")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{uuid4().hex}.mp4"

    # 5) mp4 파일로 쓰기
    #    - fps는 24로 고정 (정지 이미지라서 1장만 반복 재생됨)
    video_clip.write_videofile(
        str(output_path),
        fps=24,
    )

    # 6) 리소스 정리
    audio_clip.close()
    video_clip.close()

    return output_path