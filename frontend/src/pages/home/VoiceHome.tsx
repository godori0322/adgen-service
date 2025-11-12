import { useEffect, useRef, useState } from "react";
import PageTitle from "../../components/common/PageTitle";
import VoiceRecorder from "../../components/voice/VoiceRecorder";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export default function VoiceHomePage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const chatEnfRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    chatEnfRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [messages]);

  const onAudioSend = async (audioBlob: Blob) => {
    console.log("녹음 완료:", audioBlob);

    setLoading(true);

    // Whisper 대신 고정 텍스트 사용 (임시) -> 추후 API 연결
    const fakeUserText = "오늘 손님 없는데 뭘 올리면 좋을까?";
    setMessages((prev) => [...prev, { role: "user", content: fakeUserText }]);

    scrollToBottom();

    await new Promise((res) => setTimeout(res, 1500));

    const fakeAiReply = "추천: 복숭아 에이드 홍보 이벤트를 올려보세요!";
    setMessages((prev) => [...prev, {role: "assistant", content: fakeAiReply}]);
    setLoading(false);
  };



  return (
    <div className="relative pb-32">
      <PageTitle>🎙️ 음성 기반 마케팅 생성</PageTitle>
      {/* 채팅 bubble 영역 */}
      <div className="mt-4 space-y-3">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`max-w-[80%] px-4 py-3 rounded-2xl text-sm leading-relaxed shadow
              ${
                msg.role === "user"
                  ? "ml-auto bg-blue-500 text-white rounded-br-none"
                  : "mr-auto bg-gray-200 text-gray-900 rounded-bl-none"
              }
            `}
          >
            {msg.content}
          </div>
        ))}

        <div ref={chatEnfRef} />
      </div>
      <div className="fixed bottom-5 left-1/2 -translate-x-1/2 z-50">
        <VoiceRecorder onAudioSend={onAudioSend} />
      </div>
    </div>
  );
}
