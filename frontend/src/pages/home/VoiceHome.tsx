import { useEffect, useRef, useState } from "react";
import PageTitle from "../../components/common/PageTitle";
import VoiceRecorder from "../../components/voice/VoiceRecorder";
import { useVoiceChat } from "../../hooks/useVoiceChat";
import ChatBubbleList from "../../components/voice/ChatBubbleList";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  tempId?: number; // 임시 메시지 식별용
}

export default function VoiceHomePage() {
  const {messages, onAudioSend} = useVoiceChat();
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);


  return (
    <div className="relative pb-32">
      <PageTitle variant="section">🎙️ 음성 기반 마케팅 생성</PageTitle>
      {/* 채팅 bubble 영역 */}
      <ChatBubbleList messages={messages} />
      <div ref={chatEndRef} />
      <div className="fixed bottom-5 left-1/2 -translate-x-1/2 z-50">
        <VoiceRecorder onAudioSend={onAudioSend} />
      </div>
    </div>
  );
}
