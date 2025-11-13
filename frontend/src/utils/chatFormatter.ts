interface GptParsed {
  idea: string;
  caption: string;
  hashtags?: string[];
  image_prompt?: string;
}


export function formatChatResponse(parsed: GptParsed) {
  return `
💡 ${parsed.idea}

📝 ${parsed.caption}

🏷️ ${parsed.hashtags?.join(" ") || "(해시태그 없음)"}

🖼️ ${parsed.image_prompt || ""}
  `.trim();
}