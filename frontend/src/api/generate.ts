import { httpPostForm, httpPost } from "./http";

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
  // const imgUrl = URL.createObjectURL(adRes);
  return adRes;
}