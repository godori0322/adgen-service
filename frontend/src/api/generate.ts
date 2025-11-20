import { httpPostForm, httpPost, httpPostImg } from "./http";

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

export async function generateDialogue(userInput: string) {
  const body = {"user_input": userInput};
  return await httpPost("/gpt/dialogue", body);
}

export async function generateDiffusion(prompt: string) {
  const img = await httpPostImg("/diffusion/generate", { prompt });
  const imgSrc = URL.createObjectURL(img);
  return imgSrc;
}