import { useState } from "react";
import { useDotsAnimation } from "./useDotsAnimation";
import { useWhisper } from "./useWhisper";
import { useGptGenerate } from "./useGPTGenerate";
import { formatChatResponse } from "../utils/chatFormatter";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  tempId?: number; // 임시 메시지 식별용
}

export function useVoiceChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const {startDots, stopDots} = useDotsAnimation(setMessages);


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
        prev.map((m) => (m.tempId === userTempId ? { role: "user", content: userText } : m))
      );

      const assistantTempId = Date.now() + 1;
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: ".", tempId: assistantTempId },
      ]);
      startDots(assistantTempId);

      // gpt API 호출
      const gptParsed = await useGptGenerate(userText);
      const formatted = formatChatResponse(gptParsed);
      stopDots();
      setMessages((prev) =>
        prev.map((m) =>
          m.tempId === assistantTempId ? { role: "assistant", content: formatted } : m
        )
      );
    } catch (err: any) {
      console.error("오류:", err.message);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `음성 전송 중 오류 발생: ${err.message}` },
      ]);
    }
  };

  return { messages, onAudioSend };
}
