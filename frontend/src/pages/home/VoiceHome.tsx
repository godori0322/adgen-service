import { useEffect, useRef } from "react";
import { PageTitle } from "../../components/common/Title";
import ChatBubbleList from "../../components/voice/ChatBubbleList";
import VoiceRecorder from "../../components/voice/VoiceRecorder";
import { useVoiceChat } from "../../hooks/useVoiceChat";

export default function VoiceHomePage() {
const { messages, needImage, isWorking, onAudioSend, onImageUpload } = useVoiceChat();
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
      {/* 🔥 이미지 업로드 UI */}
      {needImage && (
        <div className="fixed bottom-24 left-1/2 -translate-x-1/2 bg-white p-4 rounded-xl shadow-xl z-50">
          <label className="cursor-pointer">
            <span className="px-4 py-2 bg-blue-600 text-white rounded-lg">📷 이미지 업로드</span>
            <input
              type="file"
              accept="image/*"
              className="hidden"
              onChange={(e) => {
                if (e.target.files?.[0]) {
                  onImageUpload(e.target.files[0]);
                }
              }}
            />
          </label>
        </div>
      )}
      {/* 🔥 이미지 필요할 땐 음성 녹음 버튼 숨김 */}
      <div className="fixed bottom-5 left-1/2 -translate-x-1/2 z-40">
        {!needImage && <VoiceRecorder onAudioSend={onAudioSend} disabled={isWorking} />}
      </div>
    </div>
  );
}
