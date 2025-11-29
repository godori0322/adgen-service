import type { ImageMode } from "../components/voice/ImageModeSelectorBubble";
import { getGuestSessionId } from "../utils/guestSession";
import { httpPostJson, httpPostJsonBlob, httpPostForm, httpPostFormBlob } from "./http";

// Whisper 음성 → 텍스트
export async function whisperTranscribeRequest(file: File) {
  const form = new FormData();
  form.append("file", file);
  return httpPostForm("/whisper/transcribe", form);
}

// GPT 마케팅 문구
export async function generateMarketingRequest(text: string, context: string | null = null) {
  return httpPostJson("/gpt/generate", { text, context });
}

// AI 광고 대화 진행
export async function generateDialogueRequest(userInput: string, isLogin: boolean) {
  const body: any = { user_input: userInput };
  if (!isLogin) body.guest_session_id = getGuestSessionId();

  return httpPostJson("/gpt/dialogue", body);
}

// Diffusion - 단일 이미지 생성
export async function generateDiffusionRequest(prompt: string, img: File) {
  const form = new FormData();
  form.append("prompt", prompt);
  form.append("product_image", img);

  const blob = await httpPostFormBlob("/diffusion/generate", form);
  return URL.createObjectURL(blob);
}

// Diffusion - 자동 합성 + BGM 옵션
export async function generateSyntheSizeDiffusionRequest(
  prompt: string,
  img: File,
  imageMode: ImageMode,
  bgmPrompt?: string
) {
  const form = new FormData();
  form.append("prompt", prompt);
  form.append("file", img);
  form.append("imageMode", imageMode);
  if (bgmPrompt) form.append("bgmPrompt", bgmPrompt);

  return httpPostFormBlob("/diffusion/synthesize/auto/upload", form);
}

// AI에게 이미지 세션 업로드
export async function uploadImage(sessionKey: string, img: File) {
  const form = new FormData();
  form.append("session_key", sessionKey);
  form.append("product_image", img);

  return httpPostForm("/gpt/dialogue/upload-image", form);
}

// 오디오 생성 (JSON → Blob)
export async function generateAudioRaw(prompt: string, durationSec: number = 20) {
  return httpPostJsonBlob("/audio/generate/raw", {
    prompt,
    duration_sec: durationSec,
  });
}
