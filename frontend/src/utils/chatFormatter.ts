interface GptParsed {
  idea: string;
  caption: string;
  hashtags?: string[];
  image_prompt?: string;
}

export function formatChatResponse(parsed: GptParsed) {
  return `
**💡 아이디어:**
${parsed.idea}\n\n

**📝 추천 캡션:** 
${parsed.caption}\n\n

**🏷️ 해시태그:** 
${parsed.hashtags?.join(" ") || "(해시태그 없음)"}\n\n
  `;
  // 🖼️ ${parsed.image_prompt || ""}
}
