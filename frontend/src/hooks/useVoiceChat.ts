import { useState } from "react";
import { generateRequest } from "../api/generate";
import { formatChatResponse } from "../utils/chatFormatter";
import { useDotsAnimation } from "./useDotsAnimation";
import { useWhisper } from "./useWhisper";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  img?: string;
  tempId?: number; // 임시 메시지 식별용
}

export function useVoiceChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const { startDots, stopDots } = useDotsAnimation(setMessages);

  const onAudioSend = async (audioBlob: Blob) => {
    // 너무 짧은 음성
    if (audioBlob.size < 10000) {
      setMessages((prev) => [
        ...prev,
        { role: "user", content: "인식할 수 없습니다. 🎤" },
        { role: "assistant", content: "음성이 너무 짧아요! 조금 더 이야기해주세요 😊" },
      ]);
      return;
    }
    try {
      const userTempId = Date.now();
      setMessages((prev) => [...prev, { role: "user", content: ".", tempId: userTempId }]);
      startDots(userTempId);

      // Whisper API 호출
      const userText = await useWhisper(audioBlob);
      stopDots();
      setMessages((prev) =>
        prev.map((m) => (m.tempId === userTempId ? { ...m, content: userText } : m))
      );
      const assistantTempId = Date.now() + 1;
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: ".", tempId: assistantTempId },
      ]);
      
      // 이미지 + generate
      startDots(assistantTempId);
      const adRes = await generateRequest(userText);
      const formatted = formatChatResponse(adRes);
      const imgSrc = `data:image/png;base64,${adRes.image_base64}`;
      setMessages((prev) =>
        prev.map((m) =>
          m.tempId === assistantTempId ? { ...m, content: formatted, img: imgSrc } : m
        )
      );
      stopDots();
    } catch (err: any) {
      console.error("오류:", err.message);
      setMessages((prev) => {
        if (prev.length === 0) {
          return [{ role: "assistant", content: `❌ 오류 발생: ${err.message}` }];
        }

        const lastIndex = prev.length - 1;

        return prev.map((m, idx) =>
          idx === lastIndex ? { ...m, content: `❌ 오류 발생: ${err.message}` } : m
        );
      });
      stopDots();
    }
  };

  return { messages, onAudioSend };
}
