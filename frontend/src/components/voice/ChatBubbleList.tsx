import type { ChatMessage } from "../../hooks/useVoiceChat";
import type { ImageMode } from "./ImageModeSelectorBubble";
import ImageModeSelectorBubble from "./ImageModeSelectorBubble";
import ShareImageButton from "../common/ShareImageButton";

export default function ChatBubbleList({
  messages,
  onSelectMode,
}: {
  messages: ChatMessage[];
  onSelectMode: (mode: ImageMode) => void;
}) {
  const downloadImage = (base64Url: string, filename: string) => {
    const link = document.createElement("a");
    link.href = base64Url;
    link.download = filename;
    link.click();
  };

  return (
    <div className="mt-4 space-y-3">
      {messages.map((msg, idx) => (
        <div
          key={idx}
          className={`max-w-[80%] px-4 py-3 rounded-2xl text-sm leading-relaxed shadow
            ${
              msg.role === "user"
                ? "ml-auto bg-blue-500 text-white rounded-br-none"
                : "mr-auto bg-gray-200 text-gray-900 rounded-bl-none"
            }`}
        >
          {msg.content && (
            <pre className="whitespace-pre-wrap font-sans text-sm">{msg.content}</pre>
          )}

          {msg.img && (
            <div className="mt-3 flex flex-col items-start gap-2">
              <img src={msg.img} alt="생성된 이미지" className="rounded-lg" />
              <div className="flex gap-2">
                <ShareImageButton imageUrl={msg.img} parsed={msg.parsed} />
                <button
                  onClick={() => downloadImage(msg.img!, `adgen-image-${Date.now()}.png`)}
                  className="bg-gray-600 hover:bg-gray-700 text-white rounded-lg px-4 py-2"
                >
                  ⬇️ 저장하기
                </button>
              </div>
            </div>
          )}

          {msg.modeSelect && <ImageModeSelectorBubble onSelect={onSelectMode} />}
        </div>
      ))}
    </div>
  );
}
