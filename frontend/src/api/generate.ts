import { getGuestSessionId } from "../utils/guestSession";
import { httpPost, httpPostForm, httpPostImg } from "./http";

export async function whisperTranscribeRequest(file: File) {
  const form = new FormData();
  form.append("file", file);
  return await httpPostForm("/whisper/transcribe", form);
}

export async function generateMarketingRequest(text: string, context: string | null = null) {
  const body = { text, context };
  return await httpPost("/gpt/generate", body);
}

export async function generateRequest(text: string, context: string | null = null) {
  const body = { text, context };
  const adRes = await httpPost("/ads/generate", body);
  return adRes;
}

export async function generateDialogueRequest(userInput: string, isLogin: boolean) {
  const body:any = { user_input: userInput };
  if(!isLogin) {
    body.guest_session_id = getGuestSessionId();
  }
  return await httpPost("/gpt/dialogue", body);
}

export async function generateDiffusionRequest(prompt: string, img: File) {
  const form = new FormData();
  form.append("prompt", prompt);
  form.append("product_image", img);
  const result = await httpPostImg("/diffusion/generate", form);
  const imgSrc = URL.createObjectURL(result);
  return imgSrc;
}
