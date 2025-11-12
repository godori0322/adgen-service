import { httpPost } from "./http";

export async function generateMarketingRequest(text: string, context: string | null = null) {
  const body = { text, context };
  return await httpPost("/gpt/generate", body);
}
