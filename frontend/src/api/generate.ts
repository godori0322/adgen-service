import type { ImageMode } from "../components/voice/ImageModeSelectorBubble";
import { getGuestSessionId } from "../utils/guestSession";
import { httpGet, httpPostForm, httpPostFormBlob, httpPostJson, httpPostJsonBlob } from "./http";

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

// Diffusion - 자동 합성 + BGM 옵션
export async function adsGenerateRequest(
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

export async function insertCaptionRequest(
  caption: string,
  font_mode: string,
  mode: string,
  width: number,
  height: number,
  textColor: { r: number; g: number; b: number },
  imgFile: File
) {
  console.log("Inserting caption with:", { caption, font_mode, mode, width, height, textColor, imgFile });
  const form = new FormData();
  form.append("text", caption);
  form.append("font_mode", font_mode);
  form.append("mode", mode);
  form.append("width", width.toString());
  form.append("height", height.toString());
  form.append("color_r", textColor.r.toString());
  form.append("color_g", textColor.g.toString());
  form.append("color_b", textColor.b.toString());
  form.append("image_file", imgFile);

  return httpPostFormBlob("/text/apply", form);
}
export async function insertCaptionPreviewRequest(caption: string, font_mode: string, mode: string, width: number, height: number, textColor: {r: number, g: number, b: number}) {
  const form = new FormData();
  form.append("text", caption);
  form.append("font_mode", font_mode);
  form.append("mode", mode);
  form.append("width", width.toString());
  form.append("height", height.toString());
  form.append("color_r", textColor.r.toString());
  form.append("color_g", textColor.g.toString());
  form.append("color_b", textColor.b.toString());

  return httpPostFormBlob("/text/preview", form);
}

// 폰트 리스트 조회
export async function getTextListRequest() {
  return httpGet("/text/fonts");
}
