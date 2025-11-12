import { generateMarketingRequest } from "../api/generate";


export async function generateGptIdea(userText: string, context: string | null = null) {
  const gptRes = await generateMarketingRequest(userText, context);
  try {
    return JSON.parse(gptRes.idea);
  } catch (err) {
    console.warn("JSON 파싱 실패");
    return {
      idea: gptRes.idea,
      caption: gptRes.caption,
      hashtags: [],
      image_prompt: "",
    };
  }

}