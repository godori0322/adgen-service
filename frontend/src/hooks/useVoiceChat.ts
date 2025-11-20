import { useState } from "react";
import { generateDialogue, generateDiffusion } from "../api/generate";
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
      
      // 이미지 + generate
      const assistantTempId = Date.now() + 1;
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: ".", tempId: assistantTempId },
      ]);
      startDots(assistantTempId);

      // 멀티턴 대화 모드
      const adRes = await generateDialogue(userText);
      stopDots();
      if (!adRes.is_complete) {
        setMessages((prev) =>
          prev.map((m) =>
            m.tempId === assistantTempId ? { ...m, content: adRes.next_question } : m
          )
        );
        return;
      }
      const formatted = formatChatResponse(adRes.final_content);
      setMessages((prev) =>
        prev.map((m) => (m.tempId === assistantTempId ? { ...m, content: formatted } : m))
      );
      if (adRes.final_content.image_prompt) {
        console.log(adRes.final_content.image_prompt);
        const imgTempId = Date.now() + 2;

        // 이미지 생성 중 메시지 추가
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: "🖼️ 이미지 생성 중입니다...", tempId: imgTempId },
        ]);

        const imgSrc = await generateDiffusion(adRes.final_content.image_prompt);

        // 이미지 채우기
        setMessages((prev) =>
          prev.map((m) => (m.tempId === imgTempId ? { ...m, content: "", img: imgSrc } : m))
        );
      }
    } catch (err: any) {
      console.error("오류:", err.message);
      const content = `❌ 오류 발생가 발생하였습니다. 다시 시도 부탁드립니다.`; 
      setMessages((prev) => {
        if (prev.length === 0) {
          return [{ role: "assistant", content }];
        }

        const lastIndex = prev.length - 1;

        return prev.map((m, idx) =>
          idx === lastIndex
            ? { ...m, content }
            : m
        );
      });
      stopDots();
    }
  };

  return { messages, onAudioSend };
}
